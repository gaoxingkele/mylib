async (page) => {
  const h6 = page.getByRole('heading', { name: /风险清单/ }).last();
  await h6.click({ force: true, timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(300);
  const copies = page.getByRole('button', { name: '复制', exact: true });
  const n = await copies.count();
  const more = page.getByRole('button', { name: '显示更多选项' });
  if (await more.count()) {
    await more.last().click({ force: true }).catch(() => {});
    await page.waitForTimeout(200);
  }
  const n2 = await copies.count();
  if (n2) await copies.last().click({ force: true });
  return { n, n2, url: page.url() };
}
