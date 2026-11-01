"""The experimental contracts beyond AGORA and DAO, written as text and act schemas.

Usage: python3 -I contracts.py <GLP clone>
Writes programs/<dir>/<NAME>.txt and <NAME>.glp for each contract below.  A schema is
given compactly: roles by name, variables typed p: (agent), s: (speech act), n: (number),
and each role as (guard, add, delete, keep, forbid), atoms written f(a, b) with R1, R2, R3
for the roles, <1>.n for the name n in role 1's namespace, and k*f(...) for k copies.
The term of a contract holds its parents' schemas first, as GSC's contracts do.
"""
import re, sys, os

GLP = sys.argv[1]

TYPES = open(f'{GLP}/programs/agora/AGORA.glp').read()
TYPES = TYPES[TYPES.index('NameTerm'):TYPES.index('%% contract_named(agora')]

PARENT_FILE = {'GKK': 'programs/gsc/GKK.glp', 'GC': 'programs/currencies/coins/GC.glp',
               'GB': 'programs/currencies/bonds/GB.glp', 'DAO': 'programs/dao/DAO.glp',
               'GSG': 'programs/gsc/GSG.glp'}


def split_top(s):
    out, depth, buf = [], 0, ''
    for ch in s:
        if ch in '([': depth += 1
        if ch in ')]': depth -= 1
        if ch == ',' and depth == 0: out.append(buf.strip()); buf = ''; continue
        buf += ch
    if buf.strip(): out.append(buf.strip())
    return out


def parent_schemas(name):
    src = open(f'{GLP}/{PARENT_FILE[name]}').read()
    body = src[src.index('contract_named('):]
    body = '\n'.join(l for l in body.split('\n') if not l.lstrip().startswith('%%'))
    env = 'environment([today]' in body
    start = body.index('environment([today],') + len('environment([today],') if env else body.index(',', body.index('contract_named('))
    lst = body[body.index('[', start):]
    depth = 0
    for i, ch in enumerate(lst):
        if ch == '[': depth += 1
        if ch == ']':
            depth -= 1
            if depth == 0: lst = lst[1:i]; break
    return env, split_top(lst)


class Contract:
    def __init__(self, name, title, dirname, extends, extends_line, preamble, clauses, pragmas, defines):
        self.name, self.title, self.dir, self.extends = name, title, dirname, extends
        self.extends_line, self.preamble, self.clauses, self.pragmas, self.defines = extends_line, preamble, clauses, pragmas, defines
        self.schemas = []

    def schema(self, name, roles, vars_, specs, constraint=None, comment='', listed=None):
        vt = {}
        for v in vars_:
            t, n = v.split(':'); vt[n] = {'p': 'pvar', 's': 'svar', 'n': 'num'}[t]
        def arg(a):
            a = a.strip()
            m = re.fullmatch(r'R(\d)', a)
            if m: return f'role({m.group(1)})'
            m = re.fullmatch(r'<(\d)>\.(\w+)', a)
            if m: return f'nterm(ext(own({m.group(1)}), {m.group(2)}))'
            return f'{vt[a]}({a})'
        def atom(t):
            t = t.strip()
            m = re.fullmatch(r'(\w+)\*(.*)', t)
            if m: return f'times(num({m.group(1)}), {atom(m.group(2))})'
            m = re.fullmatch(r'(\w+)(?:\((.*)\))?', t)
            args = split_top(m.group(2)) if m.group(2) else []
            return f'atom({m.group(1)}, [{", ".join(arg(x) for x in args)}])'
        def lst(xs): return '[' + ', '.join(atom(x) for x in xs) + ']'
        rs = []
        for sp in specs:
            g, add, dele, keep, forb = sp[:5]
            if len(sp) == 6:   # a listed role: (guard, add, del, keep, forb, (base, pred, args))
                base, pred, largs = sp[5]
                rs.append(f'crs(listed({base}, {pred}, [{", ".join(arg(x) for x in largs)}]), {g}, {lst(add)}, {lst(dele)}, {lst(keep)}, {lst(forb)})')
            else:
                rs.append(f'rs({g}, {lst(add)}, {lst(dele)}, {lst(keep)}, {lst(forb)})')
        names = '[' + ', '.join(f"'{r}'" for r in roles) + ']'
        heads = '[' + ', '.join(f'{vt[v.split(":")[1]]}({v.split(":")[1]})' for v in vars_) + ']'
        body = ',\n        '.join(rs)
        if listed:
            t = f'cschema({name}, {names}, {heads}, [],\n       [{body}])'
        elif constraint:
            t = f'nschema({name}, {names}, {heads}, {constraint},\n       [{body}])'
        else:
            t = f'schema({name}, {names}, {heads},\n       [{body}])'
        self.schemas.append(f'%% {comment}\n    {t}' if comment else '    ' + t)

    def write(self):
        d = f'{GLP}/programs/{self.dir}'
        os.makedirs(d, exist_ok=True)
        env, base, seen = False, [], set()
        for p in self.extends:
            e, ss = parent_schemas(p)
            env = env or e
            for s in ss:
                n = re.match(r'\s*[nc]?schema\((\w+)', s).group(1)
                if n not in seen: seen.add(n); base.append('    ' + s.strip())
        head = f"""%% ---------------------------------------------------------------------------
%% {self.name}.glp --- {self.title} (Nimrod Talmon with Claude, 2026-10-31), in the
%% term form programs/gsc reads.  The clauses are in {self.name}.txt beside this
%% file.  {self.name} extends {' and '.join(self.extends)}, so the term holds their schemas first,
%% as their own files give them, and then {self.name}'s own; tools/contracts.py in
%% the grassroots-contracts repository writes it.
%% ---------------------------------------------------------------------------

"""
        open_ = f'contract_named({self.name.lower()}, environment([today],\n   [' if env else f'contract_named({self.name.lower()},\n   ['
        close = '])).\n' if env else ']).\n'
        text = head + TYPES + f'%% contract_named({self.name.lower()}, C): the contract, {self.name}.\nprocedure contract_named(Constant?, Declared).\n' + \
            open_ + ',\n'.join(base).lstrip() + ',\n' + ',\n'.join(self.schemas) + close
        open(f'{d}/{self.name}.glp', 'w').write(text)
        txt = [f'% {self.name}: {self.title} --- an experimental contract by Nimrod Talmon with Claude, 2026-10-31.  Outside the owners\' process.',
               '% Owner: Nimrod (experimental).  No paper.',
               f'% Extends: {self.extends_line}',
               f'% Defines: {self.defines}',
               f'% Schemas: {self.name}.glp beside this file, written by tools/contracts.py.',
               f'{self.name}: {self.title}', self.preamble]
        txt += [f'{i}. {m} {n}.  {t}' for i, (m, n, t) in enumerate(self.clauses, 1)]
        txt += ['Pragmas'] + self.pragmas
        open(f'{d}/{self.name}.txt', 'w').write('\n'.join(txt) + '\n')
        print(self.name, len(base), '+', len(self.schemas), 'schemas')


ID = 'identity'
C = []

# ---------------------------------------------------------------- Funded DAO
c = Contract('FDAO', 'Funded DAO', 'fdao', ['DAO', 'GB'],
    'DAO, Grassroots DAO (programs/dao), and GB, Grassroots Bonds, Currencies\' (programs/currencies/bonds).  Through them it extends GKK; it cites their clauses whole and restates none.',
    'Alice and Bob are persons.  FDAO extends DAO and GB.',
    [('■', 'Funding', 'A member of a DAO may give it coins they hold; its steward, who is not asked, keeps them apart as the DAO\'s, and they leave the DAO only as grants.'),
     ('■', 'Granting', 'The steward may pay the proposer of a passed proposal, once per proposal, any amount of the DAO\'s coins of one issuer; the proposer is not asked.'),
     ('○', 'Amount', 'The steward grants a passed proposal the amount it asks for, as far as the DAO\'s coins allow.')],
    ['Treasury: the dao coins Alice keeps.', 'Grants: the granted ones Alice paid.',
     'Funding: Bob [Fund] <issuer> <amount>', '  Alice [Fund own] <issuer> <amount>',
     'Granting: Alice [Grant] <proposal> <issuer> <amount>', '  Alice [Grant own] <proposal> <issuer> <amount>'],
    'treasury, the DAO\'s coins, k.dao_coin(u, n) at its steward; grant.')
c.schema('fund', ['Bob', 'Alice'], ['p:u', 'n:k', 's:n'],
    [('guarded', [], ['k*coin(u)'], [ID, 'member(<2>.n)'], []),
     ('unguarded', ['k*dao_coin(u, n)', 'knows(u)'], [], [ID, 'member(<2>.n)', 'listed(R2, n)', 'listed(R1, n)'], [])],
    comment='FDAO:1, Funding: Bob gives k coins of u to the DAO, kept by its steward Alice.')
c.schema('fund_own', ['Alice'], ['p:u', 'n:k', 's:n'],
    [('guarded', ['k*dao_coin(u, n)'], ['k*coin(u)'], [ID, 'member(<1>.n)', 'listed(R1, n)'], [])],
    comment='FDAO:1, the steward gives coins of its own.')
c.schema('grant', ['Alice', 'Bob'], ['s:x', 'p:u', 'n:k', 's:n'],
    [('guarded', ['granted(x, R2, n)'], ['k*dao_coin(u, n)'], [ID, 'member(<1>.n)', 'listed(R1, n)', 'passed_proposal(x, R2, <1>.n)'], ['granted(x, R2, n)']),
     ('unguarded', ['k*coin(u)', 'knows(u)'], [], [ID], [])],
    comment='FDAO:2, Granting: the steward pays the proposer of a passed proposal, once.')
c.schema('grant_own', ['Alice'], ['s:x', 'p:u', 'n:k', 's:n'],
    [('guarded', ['granted(x, R1, n)', 'k*coin(u)'], ['k*dao_coin(u, n)'], [ID, 'member(<1>.n)', 'listed(R1, n)', 'passed_proposal(x, R1, <1>.n)'], ['granted(x, R1, n)'])],
    comment='FDAO:2, a grant to a passed proposal of the steward\'s own.')
C.append(c)

# ---------------------------------------------------------------- Stays
c = Contract('STAY', 'Grassroots Stays', 'stay', ['GB'],
    'GB, Grassroots Bonds, Currencies\' (programs/currencies/bonds).  Through it it extends GKK; it cites their clauses whole and restates none.',
    'Alice and Bob are persons.  STAY extends GB.',
    [('◆', 'Hosting', 'Alice, who can host guests at a place, may list it under a name not among their places.'),
     ('■', 'Booking', 'Bob, who knows Alice, and Alice may jointly decide that Bob stays at a place of Alice\'s on a night later than Alice\'s date, for a price Bob pays in Alice-coins; a place is booked at most once a night.'),
     ('■', 'Cancelling', 'Before the night, by Alice\'s date, Alice may cancel a stay, paying Bob back its whole price in Alice-coins; Bob is not asked.'),
     ('■', 'Reviewing', 'Once the night has come, by Bob\'s date, Bob may review their stay, once; Alice keeps the review and is not asked.')],
    ['Places: the places Alice hosts.', 'Stays: the stays Alice has.', 'Guests: the guests Alice hosts.', 'Reviews: the reviews Alice received.',
     'Hosting: Alice [List place] <place>',
     'Booking: Bob [Book] <place> <night> <amount>', '  Alice: Bob asks to stay at your place.',
     'Cancelling: Alice [Cancel]',
     'Reviewing: Bob [Review] <review>'],
    'place; stay, stay(x, a, d) at the guest; guest, guest(b, x, d, k) at the host, k the price; review; a night is a day of GB\'s calendar.')
c.schema('list_place', ['Alice'], ['s:x'],
    [('guarded', ['place(x)'], [], [ID], ['place(x)'])], comment='STAY:1, Hosting.')
c.schema('book', ['Bob', 'Alice'], ['s:x', 'n:d', 'n:k', 'n:t'],
    [('guarded', ['stay(x, R2, d)'], ['k*coin(R2)'], [ID, 'knows(R2)'], []),
     ('guarded', ['booked(x, d)', 'guest(R1, x, d, k)'], [], [ID, 'place(x)', 'date(t)'], ['booked(x, d)'])],
    constraint='gt(num(d), num(t))', comment='STAY:2, Booking: Bob pays k Alice-coins for the night d, later than Alice\'s date t.')
c.schema('cancel', ['Alice', 'Bob'], ['s:x', 'n:d', 'n:k', 'n:t'],
    [('guarded', [], ['booked(x, d)', 'guest(R2, x, d, k)'], [ID, 'date(t)'], []),
     ('unguarded', ['k*coin(R1)'], ['stay(x, R1, d)'], [ID], [])],
    constraint='gt(num(d), num(t))', comment='STAY:3, Cancelling, before the night: Bob is paid back the price k, in Alice-coins.')
c.schema('review', ['Bob', 'Alice'], ['s:x', 'n:d', 's:r', 'n:t'],
    [('guarded', ['reviewed(x, R2, d)'], [], [ID, 'stay(x, R2, d)', 'date(t)'], ['reviewed(x, R2, d)']),
     ('unguarded', ['review(x, R1, r)'], [], [ID], [])],
    constraint='le(num(d), num(t))', comment='STAY:4, Reviewing, after the night, once.')
C.append(c)

# ---------------------------------------------------------------- Library
c = Contract('LIB', 'Grassroots Library', 'lib', ['GB'],
    'GB, Grassroots Bonds, Currencies\' (programs/currencies/bonds), for its calendar.  Through it it extends GKK; it cites their clauses whole and restates none.',
    'Alice and Bob are persons.  LIB extends GB.',
    [('◆', 'Shelving', 'Alice may put a thing of their own on their shelf, under a name they have not used before.'),
     ('■', 'Lending', 'Alice and Bob, who know each other, may jointly decide that Alice lends Bob a thing from Alice\'s shelf until a day later than Alice\'s date; it leaves the shelf, and Bob holds it but cannot lend it on.'),
     ('■', 'Returning', 'Bob may return a borrowed thing at any time; Alice is not asked, and it goes back on Alice\'s shelf.'),
     ('○', 'On time', 'Bob returns a borrowed thing by the agreed day.')],
    ['Shelf: the things Alice has.', 'Lent: the things lent out by Alice.', 'Borrowed: what Alice borrowed.',
     'Shelving: Alice [Shelve] <thing>',
     'Lending: Alice [Lend] <thing> <until>', '  Bob: Alice offers to lend you a thing.',
     'Returning: Bob [Give back]'],
    'thing, shelf, lent out, borrowed; a day is a day of GB\'s calendar.')
c.schema('shelve', ['Alice'], ['s:x'],
    [('guarded', ['thing(R1, x)', 'owned(x)'], [], [ID], ['owned(x)'])], comment='LIB:1, Shelving.')
c.schema('lend', ['Alice', 'Bob'], ['s:x', 'n:d', 'n:t'],
    [('guarded', ['lent_out(x, R2, d)'], ['thing(R1, x)'], [ID, 'knows(R2)', 'date(t)'], []),
     ('guarded', ['borrowed(x, R1, d)'], [], [ID, 'knows(R1)'], [])],
    constraint='gt(num(d), num(t))', comment='LIB:2, Lending until the day d, later than Alice\'s date t.')
c.schema('give_back', ['Bob', 'Alice'], ['s:x', 'n:d'],
    [('guarded', [], ['borrowed(x, R2, d)'], [ID], []),
     ('unguarded', ['thing(R2, x)'], ['lent_out(x, R1, d)'], [ID], [])],
    comment='LIB:3, Returning: the thing goes back on its owner Alice\'s shelf.')
C.append(c)

# ---------------------------------------------------------------- Liquid DAO
c = Contract('LDAO', 'Liquid DAO', 'ldao', ['DAO'],
    'DAO, Grassroots DAO (programs/dao), and through it GKK.  It cites their clauses whole and restates none.',
    'Alice and Bob are persons.  LDAO extends DAO.',
    [('■', 'Delegating', 'A member of a DAO, the steward included, may make another member, whom they know, their delegate in it, one at a time; the steward records the delegation.'),
     ('■', 'Revoking', 'A member may revoke their delegation at any time; the steward erases it.'),
     ('■', 'Counting', 'Once the delegate of a member who has not voted on a proposal has a vote on it counted, the steward counts the member as voting the same way, and the member cannot vote on it any more; so a vote passes down a chain of delegates, and a member whose chain ends with no vote, or runs into a cycle, is not counted.')],
    ['Delegate: my delegate in each DAO.', 'Delegations: the delegations Alice records.',
     'Delegating: Bob [Delegate] <delegate>', '  Alice [Delegate own] <delegate>',
     'Revoking: Bob [Revoke] <delegate>', '  Alice [Revoke own] <delegate>'],
    'delegate, delegation; my_delegate(c, <a>.n) at the member, a the steward, delegation(m, c, n) at the steward; a vote counted through a delegate is recorded as the member\'s own, yes_vote or no_vote, with its ballots, and followed(x, o, b, c, n) at the steward names the delegate c whose vote b followed.')
c.schema('delegate', ['Bob', 'Alice'], ['p:c', 's:n'],
    [('guarded', ['my_delegate(c, <2>.n)', 'delegating(<2>.n)'], [], [ID, 'member(<2>.n)', 'knows(c)'], ['delegating(<2>.n)']),
     ('unguarded', ['delegation(R1, c, n)'], [], [ID, 'member(<2>.n)', 'listed(R2, n)', 'listed(R1, n)', 'listed(c, n)'], [])],
    comment='LDAO:1, Delegating: Bob makes c, a member Bob knows, their delegate.')
c.schema('revoke', ['Bob', 'Alice'], ['p:c', 's:n'],
    [('guarded', [], ['my_delegate(c, <2>.n)', 'delegating(<2>.n)'], [ID, 'member(<2>.n)'], []),
     ('unguarded', [], ['delegation(R1, c, n)'], [ID, 'member(<2>.n)'], [])],
    comment='LDAO:2, Revoking.')
c.schema('delegate_own', ['Alice'], ['p:c', 's:n'],
    [('guarded', ['my_delegate(c, <1>.n)', 'delegating(<1>.n)', 'delegation(R1, c, n)'], [], [ID, 'member(<1>.n)', 'listed(R1, n)', 'listed(c, n)', 'knows(c)'], ['delegating(<1>.n)'])],
    comment='LDAO:1, the steward delegates.')
c.schema('revoke_own', ['Alice'], ['p:c', 's:n'],
    [('guarded', [], ['my_delegate(c, <1>.n)', 'delegating(<1>.n)', 'delegation(R1, c, n)'], [ID, 'member(<1>.n)'], [])],
    comment='LDAO:2, the steward revokes.')
for side, vote, ballot in (('for', 'yes_vote', 'for_ballot'), ('against', 'no_vote', 'against_ballot')):
    c.schema(f'count_{side}', ['Alice'], ['s:x', 'p:o', 'p:b', 'p:c', 's:n'],
        [('unguarded', [f'{vote}(x, o, b, <1>.n)', 'counted(x, o, b, n)', 'followed(x, o, b, c, n)', f'2*{ballot}(x, o, n)'], [],
          [ID, 'member(<1>.n)', 'listed(R1, n)', 'proposal(x, o, <1>.n)', 'listed(b, n)', 'delegation(b, c, n)', f'{vote}(x, o, c, <1>.n)'],
          ['counted(x, o, b, n)', 'decided(x, o, <1>.n)'])],
        comment=f'LDAO:3, Counting: the steward counts b, whose delegate c has a vote {side} counted, as voting {side}; no one wills it.')
C.append(c)

# ---------------------------------------------------------------- Joint accounts
c = Contract('JOINT', 'Joint Accounts', 'joint', ['GC'],
    'GC, Grassroots Coins, Currencies\' (programs/currencies/coins), and through it GKK.  It cites their clauses whole and restates none.',
    'Alice and Bob are persons.  JOINT extends GC.',
    [('■', 'Opening', 'Alice and Bob, who know each other, may jointly open a joint account, under a name of Alice\'s not already used for one.'),
     ('■', 'Depositing', 'Either of them may move coins they hold into their joint account; the other is not asked.'),
     ('■', 'Withdrawing', 'Coins leave a joint account only by an act of both, to either of them.')],
    ['Joint: the joint money Alice shares.', 'Accounts: the accounts Alice shares.',
     'Opening: Alice [Open account] <name>', '  Bob: Alice asks to open a joint account with you.',
     'Depositing: Alice [Deposit] <issuer> <amount>',
     'Withdrawing: Alice [Withdraw] <issuer> <amount>', '  Bob: Alice asks to withdraw from your joint account.'],
    'joint account, named by its opener as a group by its leader; k.joint(u, <a>.n) at both partners.')
c.schema('open_account', ['Alice', 'Bob'], ['s:n'],
    [('guarded', ['account(<1>.n)', 'partner(R2, n)'], [], [ID, 'knows(R2)'], ['account(<1>.n)']),
     ('guarded', ['account(<1>.n)', 'partner(R1, n)'], [], [ID, 'knows(R1)'], ['account(<1>.n)'])],
    comment='JOINT:1, Opening: the account <Alice>.n, held by both.')
c.schema('deposit_opener', ['Alice', 'Bob'], ['p:u', 'n:k', 's:n'],
    [('guarded', ['k*joint(u, <1>.n)'], ['k*coin(u)'], [ID, 'account(<1>.n)', 'partner(R2, n)'], []),
     ('unguarded', ['k*joint(u, <1>.n)', 'knows(u)'], [], [ID, 'account(<1>.n)'], [])],
    comment='JOINT:2, Depositing, by the opener.')
c.schema('deposit_partner', ['Alice', 'Bob'], ['p:u', 'n:k', 's:n'],
    [('guarded', ['k*joint(u, <2>.n)'], ['k*coin(u)'], [ID, 'account(<2>.n)'], []),
     ('unguarded', ['k*joint(u, <2>.n)', 'knows(u)'], [], [ID, 'account(<2>.n)', 'partner(R1, n)'], [])],
    comment='JOINT:2, Depositing, by the partner, Bob being the opener.')
c.schema('withdraw_opener', ['Alice', 'Bob'], ['p:u', 'n:k', 's:n'],
    [('guarded', ['k*coin(u)'], ['k*joint(u, <1>.n)'], [ID, 'account(<1>.n)', 'partner(R2, n)'], []),
     ('guarded', [], ['k*joint(u, <1>.n)'], [ID, 'account(<1>.n)'], [])],
    comment='JOINT:3, Withdrawing to the opener, by an act of both.')
c.schema('withdraw_partner', ['Alice', 'Bob'], ['p:u', 'n:k', 's:n'],
    [('guarded', ['k*coin(u)'], ['k*joint(u, <2>.n)'], [ID, 'account(<2>.n)'], []),
     ('guarded', [], ['k*joint(u, <2>.n)'], [ID, 'account(<2>.n)', 'partner(R1, n)'], [])],
    comment='JOINT:3, Withdrawing to the partner, Bob being the opener, by an act of both.')
C.append(c)

# ---------------------------------------------------------------- Recommendations
c = Contract('REC', 'Recommendations', 'rec', ['GKK'],
    'GKK, Grassroots Keys and Knowledge, GSC\'s (programs/gsc).  It cites GKK:1 to GKK:3 whole and restates none.',
    'Alice, Bob and Carol are persons.  REC extends GKK.',
    [('◆', 'Recommending', 'Alice may recommend Bob, whom they know, for something, a skill or a service, once for each thing; Bob is not asked and keeps the recommendation.'),
     ('■', 'Showing', 'Bob may show a recommendation they hold to Carol, whom they know, once; Carol then sees who recommended Bob and for what, but does not thereby come to know the recommender.'),
     ('■', 'Withdrawing', 'Alice may withdraw a recommendation; it is gone from Bob and from everyone Bob showed it to, and Alice may not make it again.')],
    ['Given: the recommended people Alice vouches for.', 'Received: the endorsements Alice holds.', 'Seen: the vouched ones Alice saw.',
     'Recommending: Alice [Recommend] <for what>',
     'Showing: Bob [Show] <recommendation>',
     'Withdrawing: Alice [Withdraw recommendation]'],
    'recommendation: recommended(b, s) at the recommender, endorsement(a, s) at the recommended, shown(c, a, s) at them for each person shown, vouched(b, a, s) at that person.')
c.schema('recommend', ['Alice', 'Bob'], ['s:s'],
    [('guarded', ['recommended(R2, s)'], [], [ID, 'knows(R2)'], ['recommended(R2, s)', 'withdrew(R2, s)']),
     ('unguarded', ['endorsement(R1, s)'], [], [ID], [])],
    comment='REC:1, Recommending: Alice recommends Bob for s.')
c.schema('show', ['Bob', 'Carol'], ['p:a', 's:s'],
    [('guarded', ['shown(R2, a, s)'], [], [ID, 'endorsement(a, s)', 'knows(R2)'], ['shown(R2, a, s)']),
     ('unguarded', ['vouched(R1, a, s)'], [], [ID], [])],
    comment='REC:2, Showing: Bob shows Carol that a recommends Bob for s.')
c.schema('withdraw_recommendation', ['Bob', 'Alice', 'Bob'], ['s:s'],
    [('unguarded', [], ['endorsement(R2, s)'], [ID], []),
     ('guarded', ['withdrew(R1, s)'], ['recommended(R1, s)'], [ID], []),
     ('unguarded', [], ['vouched(R1, R2, s)'], [ID], [], (1, 'shown', ['R2', 's']))],
    comment='REC:3, Withdrawing: from Bob and from every person Bob showed it to; withdrew(b, s) keeps Alice from making it again.', listed=True)
C.append(c)

for c in C:
    c.write()
