async (page) => {
  const copies = page.getByRole('button', { name: '复制', exact: true });
  const n = await copies.count();
  if (n) await copies.last().click({ force: true, timeout: 8000 });
  await page.waitForTimeout(250);
  return { n, url: page.url() };
}
