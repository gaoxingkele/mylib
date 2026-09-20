async (page) => {
  const dismiss = page.getByRole('button', { name: /Dismiss|关闭|Not now|以后再说|Got it|OK/i });
  if (await dismiss.count()) {
    await dismiss.first().click({ force: true }).catch(() => {});
    await page.waitForTimeout(200);
  }
  const cookie = page.getByRole('button', { name: /Accept|同意|OK/i });
  if (await cookie.count()) {
    await cookie.first().click({ force: true }).catch(() => {});
  }
  const expert = page.getByRole('button', { name: /Expert/i });
  const labels = [];
  const n = await expert.count();
  for (let i = 0; i < n; i++) {
    labels.push((await expert.nth(i).innerText().catch(() => '')) || (await expert.nth(i).getAttribute('aria-label')) || '');
  }
  return {
    url: page.url(),
    title: await page.title(),
    expertCount: n,
    labels,
    hasAsk: await page.getByRole('textbox', { name: 'Ask Grok anything' }).count(),
    modelSelect: await page.getByRole('button', { name: 'Model select' }).innerText().catch(() => ''),
  };
}
