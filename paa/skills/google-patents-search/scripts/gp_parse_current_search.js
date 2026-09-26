// 解析「当前已打开」的 Google Patents 检索结果页（MCP 浏览器路线）。
//
// 用法（Playwright MCP / browser_run_code_unsafe）：
//   1) 先 browser_navigate 到检索 URL（用 gp_search.py --print-url 生成，或站点内手点）；
//   2) 再 browser_run_code_unsafe 且 filename 指向本文件（或把本文件内容粘到 code 参数）。
// 返回：{ url, title, count, hits:[{pub_number,title,text,pdf,thumbnail}] }
// 说明：结果项的公开号在 <state-modifier data-result="patent/<PN>/<lang>"> 里，最稳定。
async (page) => {
  await page.waitForTimeout(2500);
  // 结果列表懒渲染：滚动把条目带出来
  for (let i = 0; i < 2; i++) {
    await page.mouse.wheel(0, 4000);
    await page.waitForTimeout(700);
  }
  const out = await page.evaluate(() => {
    const items = [...document.querySelectorAll('search-result-item')];
    const hits = items.map(el => {
      const sm = el.querySelector('state-modifier[data-result]');
      const dr = sm ? sm.getAttribute('data-result') || '' : '';
      const m = dr.match(/patent\/([^/]+)\//);
      const a = el.querySelector('a[href$=".pdf"]');
      const img = el.querySelector('img.thumbnail');
      const h3 = el.querySelector('h3');
      return {
        pub_number: m ? m[1] : '',
        title: h3 ? (h3.innerText || '').trim() : '',
        text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 800),
        pdf: a ? a.getAttribute('href') : '',
        thumbnail: img ? img.getAttribute('src') : '',
      };
    });
    const body = (document.body ? document.body.innerText : '').slice(0, 3000);
    const blocked = /Sorry\.\.\.|automated queries|unusual traffic/i.test(body);
    return { url: location.href, title: document.title, count: hits.length, hits, blocked };
  });
  return out;
}
