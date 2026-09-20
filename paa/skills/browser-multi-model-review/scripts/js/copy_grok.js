async (page) => {
  await page.getByRole('button', { name: 'Copy response' }).click({ force: true, timeout: 10000 });
  return { ok: true, url: page.url() };
}
