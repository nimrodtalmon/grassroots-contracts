const { chromium } = require('playwright');
(async () => {
  const cs = process.argv.slice(2);
  const b = await chromium.launch();
  for (const c of cs) {
    const p = await b.newPage({viewport:{width:1400,height:1000}});
    const errs=[]; p.on('pageerror', e=>errs.push(e.message));
    const t0 = Date.now();
    try {
      await p.goto(`http://localhost:8090/app.html?c=${c}`);
      await p.click('#reset'); await p.waitForTimeout(1500);
      const ready = async () => { await p.waitForTimeout(700); await p.waitForFunction(() => document.querySelector('#stxt').textContent==='Ready', null, {timeout:240000}); await p.waitForTimeout(900); };
      await ready();
      const ph = i => p.locator('.phone').nth(i);
      for (const i of [0,1]) { await ph(i).locator('[data-prop=establish]').click(); await ready(); }
      const tab0 = await ph(0).locator('.seg button').first().textContent();
      await ph(0).locator('[data-prop=acquaint], [data-prop=meet]').first().click(); await p.waitForTimeout(300);
      await ph(0).locator('.form select').first().selectOption({index:0}); await ph(0).locator('.go').click(); await ready();
      await ph(1).locator('.yes').first().click(); await ready();
      await ph(0).locator('.seg button').first().click(); await p.waitForTimeout(300);
      const l0 = await ph(0).locator('.list').allTextContents();
      console.log(c, 'ok', `${Math.round((Date.now()-t0)/1000)}s`, 'tab', tab0, 'alice sees', JSON.stringify(l0), errs.length? 'ERR '+errs: '');
      await p.screenshot({path:`/home/claude/build/smoke-${c}.png`});
    } catch (e) { console.log(c, 'FAIL', e.message.split('\n')[0]); await p.screenshot({path:`/home/claude/build/smoke-${c}.png`}); }
    await p.close();
  }
  await b.close();
})();
