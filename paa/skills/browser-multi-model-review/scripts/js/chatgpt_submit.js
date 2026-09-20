async (page) => {
  const send = page.getByRole('button', { name: /发送提示|发送|Submit/ });
  let clicked = false;
  if (await send.count()) {
    await send.last().click({ force: true, timeout: 8000 });
    clicked = true;
  } else {
    await page.keyboard.press('Enter');
    clicked = 'enter';
  }
  await page.waitForTimeout(800);
  return { clicked, url: page.url(), title: await page.title() };
}
