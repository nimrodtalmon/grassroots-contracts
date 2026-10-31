// Live server for the grassroots contracts: for each contract, the compiled
// canonical platform (programs/vglp/cva/live_<c>), four persons, alice, bob,
// carol and dave, in one GLP heap.  The server is every person: it keeps what
// each person's dispatcher draws and injects the person's grants,
// input(Id, Path, R), from the web page.  A contract's world starts on its
// first request and is dropped after an hour without one.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:glp_runtime/multiagent/agent_runtime.dart';
import 'package:glp_runtime/runtime/terms.dart' as rt;

final persons = ['alice', 'bob', 'carol', 'dave'];

class World {
  final String contract;
  World(this.contract);
  late AgentRuntime agent;
  final Map<String, Map<int, Object?>> draws = {for (final p in persons) p: {}};
  final List<Object?> net = [];
  int version = 0;
  int day = 0;
  bool calendar = false;
  String status = 'starting';
  DateTime used = DateTime.now();
  Future<void> queue = Future.value();
  late Future<void> ready;

  Future<void> start(String root) async {
    agent = AgentRuntime(
      agentId: 'host',
      program: '$root/programs/vglp/cva/live_$contract',
      rootSelfGlpPath: '$root/programs/self.glp',
      goalLabel: 'live_ui/3',
    );
    agent.maxQuiescenceCycles = 20000000;
    agent.onUserOutput = (t) => _onOut(toJson(agent.derefTerm(t)));
    calendar = File('$root/programs/vglp/cva/live_$contract/self.glp').readAsStringSync().contains('cal(alice, N)');
    try {
      await agent.initialize();
      if (calendar) await setDay(1);
      status = 'ready';
    } catch (e) {
      status = 'failed: $e';
      stderr.writeln('[$contract] $e');
    }
    version++;
  }

  void _onOut(Object? j) {
    if (j is Map && j['f'] == 'd') {
      final args = j['a'] as List;
      final who = args[0] as String;
      final draw = args[1];
      if (draw is Map && draw['f'] == 'draw') {
        final a = draw['a'] as List;
        draws[who]![a[0] as int] = a[2];
      } else if (draw is Map && draw['f'] == 'withdraw') {
        draws[who]!.remove((draw['a'] as List)[0] as int);
      }
    } else if (j is Map && j['f'] == 'net') {
      net.add((j['a'] as List)[0]);
      if (net.length > 300) net.removeAt(0);
    }
    version++;
  }

  Future<void> act(String who, int id, List<int> path, Object? value) {
    used = DateTime.now();
    status = 'working';
    version++;
    final term = rt.StructTerm('in', [
      rt.ConstTerm(who),
      rt.StructTerm('input', [rt.ConstTerm(id), listOf(path.map((i) => rt.ConstTerm(i)).toList()), fromJson(value)]),
    ]);
    final done = queue.then((_) => agent.injectUserInput(term)).whenComplete(() {
      status = 'ready';
      version++;
    });
    queue = done.catchError((e) => stderr.writeln('[$contract] $e'));
    return done;
  }

  Future<void> setDay(int d) {
    day = d;
    version++;
    final done = queue.then((_) async {
      for (final p in persons) {
        await agent.injectUserInput(rt.StructTerm('cal', [rt.ConstTerm(p), rt.ConstTerm(d)]));
      }
    });
    queue = done.catchError((e) => stderr.writeln('[$contract] $e'));
    return done;
  }

  Map<String, Object?> state() => {
        'version': version,
        'status': status,
        if (calendar) 'day': day,
        'persons': {for (final p in persons) p: draws[p]!.map((k, v) => MapEntry('$k', v))},
        'net': net.length > 60 ? net.sublist(net.length - 60) : net,
      };
}

rt.Term listOf(List<rt.Term> items) =>
    items.reversed.fold<rt.Term>(rt.ConstTerm(rt.nil), (tail, x) => rt.StructTerm('.', [x, tail]));

Object? toJson(rt.Term t) {
  if (t is rt.ConstTerm) {
    if (t.value == rt.nil || t.value == null) return <Object?>[];
    final v = t.value;
    if (v is num || v is String || v is bool) return v;
    return v.toString();
  }
  if (t is rt.StructTerm) {
    if (t.functor == '.' && t.args.length == 2) {
      final out = <Object?>[];
      rt.Term cur = t;
      while (cur is rt.StructTerm && cur.functor == '.' && cur.args.length == 2) {
        out.add(toJson(cur.args[0]));
        cur = cur.args[1];
      }
      if (!(cur is rt.ConstTerm && (cur.value == rt.nil || cur.value == null))) out.add({'tail': toJson(cur)});
      return out;
    }
    return {'f': t.functor, 'a': [for (final a in t.args) toJson(a)]};
  }
  return {'v': 1};
}

rt.Term fromJson(Object? j) {
  if (j is List) return listOf([for (final x in j) fromJson(x)]);
  if (j is Map) return rt.StructTerm(j['f'] as String, [for (final a in (j['a'] as List)) fromJson(a)]);
  return rt.ConstTerm(j);
}

final worlds = <String, World>{};
late String root;
late Set<String> contracts;

World world(String c) {
  var w = worlds[c];
  if (w == null) {
    // keep at most MAX_WORLDS contracts running (small hosts): drop the least recently used
    final cap = int.tryParse(Platform.environment['MAX_WORLDS'] ?? '') ?? 3;
    while (worlds.length >= cap) {
      final old = worlds.entries.reduce((a, b) => a.value.used.isBefore(b.value.used) ? a : b).key;
      worlds.remove(old);
    }
    w = World(c);
    worlds[c] = w;
    w.ready = w.start(root);
  }
  w.used = DateTime.now();
  return w;
}

Future<void> main(List<String> args) async {
  root = Platform.environment['GLP_ROOT'] ?? Directory.current.parent.path;
  final port = int.parse(Platform.environment['PORT'] ?? '8080');
  final webDir = Platform.environment['WEB_DIR'] ?? '$root/live_server/web';
  contracts = Directory('$root/programs/vglp/cva')
      .listSync()
      .whereType<Directory>()
      .map((d) => d.path.split('/').last)
      .where((n) => n.startsWith('live_'))
      .map((n) => n.substring(5))
      .toSet();
  Timer.periodic(const Duration(minutes: 5), (_) {
    final cut = DateTime.now().subtract(const Duration(hours: 1));
    worlds.removeWhere((c, w) => w.used.isBefore(cut));
  });
  final server = await HttpServer.bind(InternetAddress.anyIPv4, port);
  stdout.writeln('live server on $port: ${contracts.join(', ')}');
  await for (final req in server) {
    unawaited(handle(req, webDir));
  }
}

Future<void> handle(HttpRequest req, String webDir) async {
  try {
    req.response.headers.set('Access-Control-Allow-Origin', '*');
    final seg = req.uri.pathSegments;
    if (seg.length >= 3 && seg[0] == 'api') {
      final c = seg[1];
      if (!contracts.contains(c)) {
        req.response.statusCode = 404;
        await req.response.close();
        return;
      }
      final op = seg[2];
      var w = world(c);
      if (op == 'state') {
        final since = int.tryParse(req.uri.queryParameters['since'] ?? '') ?? -1;
        final until = DateTime.now().add(const Duration(seconds: 20));
        while (w.version == since && DateTime.now().isBefore(until)) {
          await Future.delayed(const Duration(milliseconds: 150));
        }
        _json(req, w.state());
      } else if (op == 'act' && req.method == 'POST') {
        final body = jsonDecode(await utf8.decodeStream(req)) as Map;
        await w.ready;
        unawaited(w.act(body['person'] as String, body['id'] as int,
            [for (final x in body['path'] as List) x as int], body['value']));
        _json(req, {'ok': true});
      } else if (op == 'day' && req.method == 'POST') {
        await w.ready;
        if (w.calendar) unawaited(w.setDay(w.day + 1));
        _json(req, {'ok': true});
      } else if (op == 'reset' && req.method == 'POST') {
        worlds.remove(c);
        world(c);
        _json(req, {'ok': true});
      } else {
        req.response.statusCode = 404;
        await req.response.close();
      }
      return;
    }
    final path = req.uri.path == '/' ? '/index.html' : req.uri.path;
    final f = File('$webDir$path');
    if (!path.contains('..') && await f.exists()) {
      req.response.headers.contentType = path.endsWith('.js')
          ? ContentType('application', 'javascript', charset: 'utf-8')
          : path.endsWith('.json')
              ? ContentType.json
              : path.endsWith('.html')
                  ? ContentType.html
                  : ContentType('text', 'plain', charset: 'utf-8');
      await req.response.addStream(f.openRead());
      await req.response.close();
    } else {
      req.response.statusCode = 404;
      await req.response.close();
    }
  } catch (e, st) {
    stderr.writeln('$e\n$st');
    try {
      req.response.statusCode = 500;
      req.response.write('$e');
      await req.response.close();
    } catch (_) {}
  }
}

void _json(HttpRequest req, Object? o) {
  req.response.headers.contentType = ContentType.json;
  req.response.headers.set('Cache-Control', 'no-store');
  req.response.write(jsonEncode(o));
  req.response.close();
}
