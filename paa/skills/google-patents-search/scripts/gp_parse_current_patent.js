// 解析「当前已打开」的 Google Patents 单件说明书页（MCP 浏览器路线，核验腿）。
//
// 用法（Playwright MCP / browser_run_code_unsafe）：
//   1) 先 browser_navigate 到 https://patents.google.com/patent/<PN>/<lang>；
//   2) 再 browser_run_code_unsafe 且 filename 指向本文件（或粘到 code 参数）。
// 返回：{ url, meta, abstract, claims:[{no,text}], description, counts }
// 说明：权利要求在 #claims 内（`.claim` 或 id 以 CLM- 开头的元素），说明书在 #description。
async (page) => {
  await page.waitForTimeout(2500);
  return await page.evaluate(() => {
    const meta = (n) => {
      const e = document.querySelector(`meta[name="${n}"]`);
      return e ? (e.getAttribute('content') || '').trim() : '';
    };
    const claims = [...document.querySelectorAll('#claims .claim, #claims [id^="CLM-"]')]
      .map(el => {
        const t = (el.innerText || '').trim();
        const m = t.match(/^(\d+)\s*[.、]/);
        return { no: m ? parseInt(m[1], 10) : 0, text: t };
      })
      .filter(c => c.text.length > 30);
    const descEl = document.getElementById('description');
    const absEl = document.querySelector('#abstract, [itemprop="abstract"]');
    return {
      url: location.href,
      meta: {
        pub_number: meta('citation_patent_publication_number'),
        title: meta('DC.title'),
        date: meta('DC.date'),
        contributor: meta('DC.contributor'),
      },
      abstract: absEl ? (absEl.innerText || '').trim() : '',
      claims,
      claim_count: claims.length,
      description: descEl ? (descEl.innerText || '').trim() : '',
      counts: {
        patent_citations: document.querySelectorAll('#patentCitations tr').length,
        cited_by: document.querySelectorAll('#citedBy tr').length,
        similar: document.querySelectorAll('#similarDocuments tr').length,
      },
    };
  });
}
