async (page) => {
  // 等待网页模型生成结束。只在 Playwright 进程内轮询，返回极小的状态对象，不把页面内容带回模型上下文。
  // done:false 时直接再调用一次本脚本（Grok Expert / Kimi 学术检索常需多次）。
  const MAX_MS = 150000;      // 单次调用上限，留足 MCP 超时余量
  const INTERVAL_MS = 30000;  // 30 秒查一次：检查在进程内进行，不耗 token；间隔长可避免 Grok/Kimi 检索停顿被误判为完成
  const STABLE_ROUNDS = 1;    // 相隔 30 秒两次正文长度相同且无"停止"按钮才算完成

  const host = new URL(page.url()).hostname;
  const site = /chatgpt/.test(host) ? 'chatgpt'
    : /gemini/.test(host) ? 'gemini'
    : /grok/.test(host) ? 'grok'
    : /perplexity/.test(host) ? 'pplx'
    : /kimi/.test(host) ? 'kimi'
    : host;

  const probe = () => page.evaluate(() => {
    const stopRe = /^(停止|停止回答|停止生成|停止输出|Stop|Stop generating|Stop response|Stop streaming)$/i;
    const btns = Array.from(document.querySelectorAll('button,[role="button"]'));
    const label = (b) => ((b.getAttribute('aria-label') || '') + '|' + (b.innerText || '')).split('|').map(s => s.trim());
    const generating = btns.some(b => label(b).some(t => stopRe.test(t)));
    const hasCopyReply = btns.some(b => label(b).some(t => t === '复制回复'));
    return { len: (document.body.innerText || '').length, generating, hasCopyReply };
  });

  const start = Date.now();
  let last = -1;
  let stable = 0;
  let s = { len: 0, generating: false, hasCopyReply: false };
  while (Date.now() - start < MAX_MS) {
    s = await probe();
    stable = (!s.generating && s.len === last) ? stable + 1 : 0;
    last = s.len;
    if (stable >= STABLE_ROUNDS) {
      if (site === 'chatgpt' && !s.hasCopyReply) {
        return { site, done: false, reason: 'no_reply_button', hint: 'run chatgpt_continue.js', elapsedSec: Math.round((Date.now() - start) / 1000), len: s.len };
      }
      return { site, done: true, reason: 'stable', elapsedSec: Math.round((Date.now() - start) / 1000), len: s.len };
    }
    await page.waitForTimeout(INTERVAL_MS);
  }
  return { site, done: false, reason: s.generating ? 'still_generating' : 'still_changing', hint: 'call wait_done.js again', elapsedSec: Math.round((Date.now() - start) / 1000), len: s.len };
}
