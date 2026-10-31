const { chromium } = require('playwright');
(async () => {
  const c = process.argv[2];
  const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1400,height:1100}});
  const errs=[]; p.on('pageerror', e=>errs.push(e.message));
  await p.goto((process.env.BASE||'http://localhost:8090')+`/app.html?c=${c}`);
  await p.click('#reset'); await p.waitForTimeout(1500);
  const ready = async () => { await p.waitForFunction(() => document.querySelector('#stxt').textContent!=='Ready', null, {timeout:8000}).catch(()=>{}); await p.waitForFunction(() => document.querySelector('#stxt').textContent==='Ready', null, {timeout:600000}); await p.waitForTimeout(900); };
  await ready();
  const ph = i => p.locator('.phone').nth(i);
  const step = async (i, tab, prop, fills=[], selects=[], variant=null) => {
    if (tab) await ph(i).locator(`[data-tab="${tab}"]`).click();
    await ph(i).locator(`[data-prop=${prop}]`).click(); await p.waitForTimeout(300);
    if (variant) { await ph(i).locator('[data-variant]').selectOption(variant); await p.waitForTimeout(300); }
    for (const [k,v] of selects) await ph(i).locator('.form select:not([data-variant])').nth(k).selectOption({label:v});
    for (const [k,v] of fills) await ph(i).locator('.form input').nth(k).fill(v);
    if (await ph(i).locator('.go').count()) await ph(i).locator('.go').click();
    await ready();
  };
  const yes = async i => { await ph(i).locator('.yes').first().click(); await ready(); };
  const list = async (i, tab) => { await ph(i).locator(`[data-tab="${tab}"]`).click(); await p.waitForTimeout(200); return (await ph(i).locator('.list li, .empty').allTextContents()).join(' | '); };
  await step(0,null,'establish'); await step(1,null,'establish');
  await p.locator('.phone').nth(0).locator('[data-prop=acquaint], [data-prop=meet]').first().click(); await p.waitForTimeout(300); await ph(0).locator('.go').click(); await ready(); await yes(1);
  if (c === 'gc') {
    await step(0,'Coins','mint',[[0,'5']]);
    await step(0,'Coins','pay',[[0,'2']]).catch(e=>console.log('pay form', e.message.split('\n')[0]));
    console.log('alice coins', await list(0,'Coins'));
    await step(1,'Coins','mint',[[0,'3']]);
    await step(0,'Coins','swap',[[0,'1'],[1,'1']],[[0,'Bob'],[1,'Alice'],[2,'Bob']]).catch(e=>console.log('swap', e.message.split('\n')[0]));
    await p.waitForTimeout(500); if (await ph(1).locator('.yes').count()) await yes(1);
    console.log('after swap alice', await list(0,'Coins'), 'bob', await list(1,'Coins'));
  }
  if (c === 'gsn') {
    await step(0,'Friends','befriend'); await p.screenshot({path:'/home/claude/build/gsn-bef.png'});
    console.log('bob asks', await ph(1).locator('.ask').count(), 'alice pend', await ph(0).locator('.pend, .note').allTextContents());
    await yes(1);
    await step(0,'Groups','create',[[0,'chess']]);
    await step(0,'Groups','join'); await p.screenshot({path:'/home/claude/build/gsn-join.png'});
    console.log('alice', (await ph(0).locator('details.raw pre').textContent()).replace(/\n/g,' ; '), 'notes', await ph(0).locator('.pend, .note').allTextContents());
    await yes(1);
    await step(1,'Groups','post',[[0,'hello all']]);
    console.log('alice groups', await list(0,'Groups'), '| bob groups', await list(1,'Groups'));
    console.log('alice state', (await ph(0).locator('details.raw pre').textContent()).replace(/\n/g,' ; '));
  }
  if (c === 'gff') {
    await step(0,'Friends','befriend'); await yes(1);
    console.log('tabs', await ph(0).locator('.seg button').allTextContents());
    await step(1,'Posts','post',[[0,'first post']]).catch(e=>console.log('post', e.message.split('\n')[0]));
    console.log('alice feeds', await list(0,'Feeds'), '| bob posts', await list(1,'Posts'));
    console.log('alice state', (await ph(0).locator('details.raw pre').textContent()).replace(/\n/g,' ; '));
  }
  if (c === 'agora') {
    await step(0,'Items','make',[[0,'jam']]); await step(1,'Items','make',[[0,'bike']]);
    await step(0,'Items','open',[[0,'market']]);
    await step(0,'Items','admit'); await yes(1);
    await step(1,'Items','offer');
    await step(0,'Items','offer_own');
    await step(0,'Items','want_own',[[0,'a hat']]);
    console.log('KEEPER offers', await list(0,'Offers'), '|| BOB offers', await list(1,'Offers'), '|| BOB wants', await list(1,'Wants'));
    await ph(0).locator('[data-tab="Items"]').click(); await ph(0).locator('[data-prop=withdraw_own_want]').click(); await p.waitForTimeout(300);
    console.log('FORM', (await ph(0).locator('.form').innerText()).replace(/\n/g,' / '));
    await ph(0).locator('.go').click(); await ready();
    console.log('NOTES', await ph(0).locator('.note').allTextContents());
    await ph(1).locator('[data-tab="Items"]').click(); await ph(1).locator('[data-prop=withdraw_offer]').click(); await p.waitForTimeout(300);
    await ph(1).locator('.form select:not([data-variant])').nth(1).selectOption({label:'Bob'}, {timeout:3000}).catch(e=>console.log('sel', e.message.split('\n')[0]));
    await ph(1).locator('.form input').first().fill('bike'); console.log('BOBFORM', (await ph(1).locator('.form').innerText()).replace(/\n/g,' / '));
    await ph(1).locator('.go').click(); await ready();
    console.log('after bob withdraw: KEEPER offers', await list(0,'Offers'));
    console.log('after withdraw: BOB wants', await list(1,'Wants'), '|| KEEPER wants', await list(0,'Wants'));
  }
  if (c === 'dao') {
    console.log('tabs', await ph(0).locator('.seg button').allTextContents());
    await step(0,'DAOs','found',[[0,'town']]);
    await step(0,'DAOs','admit'); await yes(1);
    await step(1,'DAOs','propose',[[0,'build a park']]);
    await step(0,'DAOs','propose_own',[[0,'plant trees']]);
    console.log('STEWARD proposals', await list(0,'Proposals'), '|| BOB proposals', await list(1,'Proposals'));
    await step(1,'DAOs','vote_for');
    await step(0,'DAOs','vote_own_against');
    console.log('STEWARD for', await list(0,'For'), '|| against', await list(0,'Against'));
    await step(0,'DAOs','pass');
    console.log('BOB passed', await list(1,'Passed'), '|| STEWARD passed', await list(0,'Passed'));
  }
  if (c === 'cssn') {
    console.log('tabs', await ph(0).locator('.seg button').allTextContents());
    await ph(0).locator('[data-tab="Children"]').click(); await p.waitForTimeout(200);
    console.log('children acts', (await ph(0).locator('.ab').allTextContents()).join(','));
    await ph(0).locator('[data-prop=enter]').click(); await p.waitForTimeout(300);
    await ph(0).locator('.form select').first().selectOption({label:'Carol'}); await ph(0).locator('.go').click(); await ready();
    console.log('carol asks', await ph(2).locator('.ask').allTextContents());
    if (await ph(2).locator('.yes').count()) await yes(2);
    console.log('alice children', await list(0,'Children'), '| carol state', (await ph(2).locator('details.raw pre').textContent()).replace(/\n/g,' ; '));
  }
  await p.screenshot({path:`/home/claude/build/deep-${c}.png`});
  console.log(c, 'errors', errs);
  await b.close();
})();
