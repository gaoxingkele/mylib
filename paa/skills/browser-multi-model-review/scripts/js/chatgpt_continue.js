async (page) => {
  const text = '请继续完成尚未写完的六节。从中断处接着写技术方案抓手、新颖性、创造性三步法、自洽、A/B/C/D建议、风险清单。只评本案。不要编造专利号。';
  const box = page.getByRole('textbox', { name: '与 ChatGPT 聊天' });
  await box.click({ force: true });
  await page.keyboard.insertText(text);
  await page.waitForTimeout(200);
  const send = page.getByRole('button', { name: /发送提示|发送/ });
  if (await send.count()) await send.last().click({ force: true });
  else await page.keyboard.press('Enter');
  await page.waitForTimeout(500);
  return { url: page.url(), title: await page.title() };
}
