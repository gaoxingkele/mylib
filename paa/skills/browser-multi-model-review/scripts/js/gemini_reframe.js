async (page) => {
  const text = [
    '澄清：这不是法律咨询、授权保证或代理意见。',
    '请把本会话上文当作已经写好的计算机系统技术文档，做结构化技术审阅。',
    '按先前给出的六节结构作答。不要给法律建议；不要编造专利号。',
    '新颖性与创造性结论只能三选一：达到 / 有条件达到 / 未达到。',
    '请现在输出完整六节。',
  ].join('');
  const box = page.getByRole('textbox', { name: '为 Gemini 输入提示' });
  await box.click({ force: true });
  await page.keyboard.insertText(text);
  await page.waitForTimeout(300);
  const send = page.getByRole('button', { name: '发送' });
  if (await send.count()) {
    await send.last().click({ force: true });
  }
  await page.waitForTimeout(500);
  return { url: page.url(), title: await page.title() };
}
