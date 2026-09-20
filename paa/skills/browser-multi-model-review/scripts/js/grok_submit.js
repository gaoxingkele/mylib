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
  await page.getByRole('button', { name: 'Submit' }).click({ force: true, timeout: 10000 });
  await page.waitForTimeout(800);
  return { url: page.url(), title: await page.title() };
}
