async (page) => {
  const m2 = page.getByRole('menuitem', { name: /模型 2/ });
  await m2.click({ force: true });
  await page.waitForTimeout(250);
  const opus = page.getByRole('menuitemradio', { name: /Claude Opus 5 Max/ });
  await opus.click({ force: true });
  await page.waitForTimeout(200);
  const think = page.getByRole('menuitemcheckbox', { name: '正在思考' });
  if (await think.count()) {
    const checked = await think.first().getAttribute('aria-checked').catch(() => null);
    if (checked !== 'true') await think.first().click({ force: true });
  }
  await page.waitForTimeout(200);
  const m3 = page.getByRole('menuitem', { name: /模型 3/ });
  await m3.click({ force: true });
  await page.waitForTimeout(250);
  const gem = page.getByRole('menuitemradio', { name: /Gemini 3.8 Flash/ });
  await gem.click({ force: true });
  await page.waitForTimeout(200);
  if (await think.count()) {
    const checked2 = await think.first().getAttribute('aria-checked').catch(() => null);
    if (checked2 !== 'true') await think.first().click({ force: true });
  }
  await page.waitForTimeout(200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  const submit = page.getByRole('button', { name: '提交' });
  const disabled = (await submit.count()) ? await submit.first().isDisabled().catch(() => true) : true;
  return {
    url: page.url(),
    submitDisabled: disabled,
    m2: await m2.innerText().catch(() => ''),
    m3: await m3.innerText().catch(() => ''),
  };
}
