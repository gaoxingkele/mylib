async (page) => {
  const submit = page.getByRole('button', { name: '提交' });
  await submit.click({ force: true, timeout: 8000 });
  await page.waitForTimeout(1200);
  return { url: page.url(), title: await page.title() };
}
