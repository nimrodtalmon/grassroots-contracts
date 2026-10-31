// End-to-end flows for the six new contracts, through the app page.
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://localhost:8090';
(async () => {
  const c = process.argv[2];
  const b = await chromium.launch(); const p = await b.newPage({viewport: {width: 1400, height: 1100}});
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(`${BASE}/app.html?c=${c}`);
  await p.click('#reset'); await p.waitForTimeout(1500);
  const ready = async () => {
    await p.waitForFunction(() => document.querySelector('#stxt').textContent !== 'Ready', null, {timeout: 6000}).catch(() => {});
    await p.waitForFunction(() => document.querySelector('#stxt').textContent === 'Ready', null, {timeout: 600000});
    await p.waitForTimeout(900);
  };
  await ready();
  const P = ['alice', 'bob', 'carol', 'dave'];
  const ph = i => p.locator('.phone').nth(i);
  const tab = async (i, t) => { await ph(i).locator(`[data-tab="${t}"]`).click(); await p.waitForTimeout(150); };
  // step: open an act on a phone, choose its variant, set selects by label and inputs, propose
  const step = async (i, t, prop, {sel = {}, fill = [], variant} = {}) => {
    if (process.env.TRACE) console.log('  step', i, t, prop);
    if (t) await tab(i, t);
    await ph(i).locator(`[data-prop="${prop}"]`).click(); await p.waitForTimeout(300);
    if (variant){ await ph(i).locator('[data-variant]').selectOption(variant); await p.waitForTimeout(300); }
    const labels = await ph(i).locator('.form label').allTextContents();
    for (const [lab, val] of Object.entries(sel)) {
      const k = labels.findIndex(x => x.toLowerCase() === lab.toLowerCase()); if (k < 0) { console.log('  no field', lab, 'in', labels); continue; }
      const field = ph(i).locator('.form label').nth(k).locator('xpath=following-sibling::*[1]');
      await field.selectOption({label: val}).catch(async () => { const opts = await field.locator('option').allTextContents(); const o = opts.find(x => x.includes(val)); if (o) await field.selectOption({label: o}); else console.log('  no option', val, 'in', opts); });
    }
    for (const [k, v] of fill) await ph(i).locator('.form input').nth(k).fill(v);
    if (await ph(i).locator('.go').count()) await ph(i).locator('.go').click();
    await ready();
  };
  const yes = async i => { for (let n = 0; n < 20 && !(await ph(i).locator('.yes').count()); n++) await p.waitForTimeout(500); await ph(i).locator('.yes').first().click(); await ready(); };
  const list = async (i, t) => { await tab(i, t); return (await ph(i).locator('.list li, .empty').allTextContents()).join(' | '); };
  const raw = async i => (await ph(i).locator('details.raw pre').textContent()).replace(/\n/g, ' ; ');
  const meet = async (i, j) => { await step(i, 'Contacts', 'acquaint', {sel: {person: P[j][0].toUpperCase() + P[j].slice(1)}}); await yes(j); };
  for (const i of [0, 1, 2]) await step(i, null, 'establish');
  await meet(0, 1); await meet(1, 2); await meet(0, 2);
  const nextDay = async () => { await p.click('#nextday'); await ready(); };
  if (c === 'fdao' || c === 'ldao') {
    await step(0, 'DAOs', 'found', {fill: [[0, 'town']]});
    await step(0, 'DAOs', 'admit', {sel: {person: 'Bob'}}); await yes(1);
    await step(0, 'DAOs', 'admit', {sel: {person: 'Carol'}}); await yes(2);
  }
  if (c === 'fdao') {
    await step(1, 'Coins', 'mint_coin', {fill: [[0, '10']]});
    await step(1, 'Treasury', 'fund', {sel: {issuer: 'Bob'}, fill: [[0, '6']]});
    console.log('STEWARD treasury', await list(0, 'Treasury'), '| BOB coins', await list(1, 'Coins'));
    await step(2, 'DAOs', 'propose', {fill: [[0, 'a bench']]});
    await step(1, 'DAOs', 'vote_for'); await step(2, 'DAOs', 'vote_for');
    await step(0, 'DAOs', 'pass');
    await step(0, 'Treasury', 'grant', {sel: {person: 'Carol', issuer: 'Bob'}, fill: [[0, '4']]});
    console.log('STEWARD treasury', await list(0, 'Treasury'), '| grants', await list(0, 'Grants'), '| CAROL coins', await list(2, 'Coins'));
  }
  if (c === 'ldao') {
    await step(1, 'Delegate', 'delegate', {sel: {delegate: 'Carol'}});
    console.log('STEWARD delegations', await list(0, 'Delegations'), '| BOB delegate', await list(1, 'Delegate'));
    await step(1, 'Delegate', 'revoke');
    console.log('after revoke: STEWARD', await list(0, 'Delegations'), '| BOB', await list(1, 'Delegate'));
  }
  if (c === 'stay') {
    await step(0, 'Places', 'list_place', {fill: [[0, 'cabin']]});
    await step(0, 'Coins', 'mint_coin', {fill: [[0, '5']]});
    await step(1, 'Coins', 'mint_coin', {fill: [[0, '5']]});
    await step(0, 'Coins', 'swap_cc', {sel: {person: 'Bob', 'issuer given': 'Alice', 'issuer wanted': 'Bob'}, fill: [[0, '3'], [1, '3']]}); await yes(1);
    console.log('BOB coins', await list(1, 'Coins'));
    await step(1, 'Places', 'book', {sel: {person: 'Alice'}, fill: [[0, 'cabin'], [1, '3'], [2, '2']]}); await yes(0);
    console.log('ALICE guests', await list(0, 'Guests'), '| BOB stays', await list(1, 'Stays'), '| BOB coins', await list(1, 'Coins'));
    await nextDay(); await nextDay(); await nextDay();
    await step(1, 'Places', 'review', {fill: [[0, 'lovely']]});
    console.log('ALICE reviews', await list(0, 'Reviews'));
  }
  if (c === 'lib') {
    await step(0, 'Shelf', 'shelve', {fill: [[0, 'drill']]});
    await step(0, 'Shelf', 'lend', {sel: {person: 'Bob'}, fill: [[0, '5']]}); await yes(1);
    console.log('ALICE shelf', await list(0, 'Shelf'), '| lent', await list(0, 'Lent'), '| BOB borrowed', await list(1, 'Borrowed'));
    await step(1, 'Shelf', 'give_back');
    console.log('after return: ALICE shelf', await list(0, 'Shelf'), '| BOB borrowed', await list(1, 'Borrowed'));
  }
  if (c === 'joint') {
    await step(0, 'Joint', 'open_account', {sel: {person: 'Bob'}, fill: [[0, 'house']]}); await yes(1);
    await step(0, 'Coins', 'mint', {fill: [[0, '5']]});
    console.log('ALICE accounts', await list(0, 'Accounts'), '| coins', await list(0, 'Coins'));
    await tab(0, 'Joint'); await ph(0).locator('[data-prop="deposit_opener"]').click(); await p.waitForTimeout(300);
    console.log('FORM', (await ph(0).locator('.form').innerText()).replace(/\n/g, ' / '));
    await ph(0).locator('[data-prop="deposit_opener"]').click(); await p.waitForTimeout(200);
    await step(0, 'Joint', 'deposit_opener', {sel: {person: 'Bob', issuer: 'Alice'}, fill: [[0, '3']]});
    console.log('NOTES', await ph(0).locator('.note').allTextContents(), await raw(0));
    console.log('ALICE joint', await list(0, 'Joint'), '| BOB joint', await list(1, 'Joint'));
    await step(1, 'Joint', 'withdraw_opener', {variant: 'withdraw_partner', fill: [[0, '2']]}); await yes(0);
    console.log('after withdraw: BOB coins', await list(1, 'Coins'), '| ALICE joint', await list(0, 'Joint'));
  }
  if (c === 'rec') {
    await step(0, 'Given', 'recommend', {sel: {person: 'Bob'}, fill: [[0, 'plumbing']]});
    console.log('BOB received', await list(1, 'Received'));
    await step(1, 'Given', 'show', {sel: {person: 'Carol'}});
    console.log('CAROL seen', await list(2, 'Seen'));
    await step(0, 'Given', 'withdraw_recommendation');
    console.log('after withdraw: BOB', await list(1, 'Received'), '| CAROL', await list(2, 'Seen'));
  }
  await p.screenshot({path: `/home/claude/build/flow-${c}.png`});
  console.log(c, 'errors', errs);
  await b.close();
})().catch(async e => { console.log('FAIL', e.message.split('\n').slice(0,3).join(' / ')); process.exit(1); });
