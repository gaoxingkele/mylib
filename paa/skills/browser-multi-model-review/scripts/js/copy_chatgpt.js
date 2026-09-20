async (page) => {
  const reply = page.getByRole('button', { name: '复制回复' });
  const n = await reply.count();
  await reply.last().click({ force: true, timeout: 12000 });
  await page.waitForTimeout(250);
  return { n, url: page.url() };
}
