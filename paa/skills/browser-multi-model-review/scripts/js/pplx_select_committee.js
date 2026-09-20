async (page) => {
  const slash = page.locator('[contenteditable="true"]').last();
  await slash.click({ force: true });
  await page.keyboard.type('/');
  await page.waitForTimeout(400);
  const item = page.getByRole('menuitemradio', { name: /委员会/ });
  const n = await item.count();
  let clicked = false;
  if (n) {
    await item.first().click({ force: true });
    clicked = true;
  } else {
    const labels = [];
    const radios = page.getByRole('menuitemradio');
    const c = await radios.count();
    for (let i = 0; i < c; i++) {
      labels.push(((await radios.nth(i).innerText().catch(() => '')) || '').replace(/\s+/g, ' ').slice(0, 80));
    }
    return { n, labels, url: page.url() };
  }
  await page.waitForTimeout(400);
  return { n, clicked, url: page.url() };
}
