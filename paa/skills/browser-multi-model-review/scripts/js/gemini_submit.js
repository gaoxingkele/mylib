async (page) => {
  const candidates = [
    page.getByRole('button', { name: '发送' }),
    page.getByRole('button', { name: /发送提示/ }),
    page.locator('button[aria-label*="发送"]'),
    page.locator('button[aria-label*="Send"]'),
  ];
  let clicked = false;
  let name = '';
  for (const loc of candidates) {
    const n = await loc.count();
    if (!n) continue;
    const last = loc.last();
    if (await last.isEnabled().catch(() => false)) {
      await last.click({ force: true, timeout: 8000 });
      clicked = true;
      name = '发送';
      break;
    }
  }
  await page.waitForTimeout(800);
  return { clicked, name, url: page.url(), title: await page.title() };
}
