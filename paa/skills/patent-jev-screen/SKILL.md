---
name: patent-jev-screen
description: >
  用 JEV 对一篇已公开专利或论文做要素判别，服务中国发明专利的新颖性与创造性研判。
  输入是独权里的若干句目标特征，加上该文献的标题、摘要或已定位段落；输出每句特征的成立概率和下一步动作。
  用于专利判别、独创性排查、创造性三步法、对比文件筛选、X/Y/A 前的要素门。
  检索仍走 incopat-search、google-patents-search 和 npl-prior-art-search。本技能不证明新颖性、创造性或授权率。
  Use when the user runs /patent-jev-screen or asks to judge whether a prior-art document discloses claim elements.
---

# 专利要素判别（JEV）

本技能接在检索之后、`patent-grant-scorer` 打分之前。它只判断一篇已公开文献有没有写出给定特征。新颖性、创造性和授权结论仍按 `paa/references/novelty-inventive-step-full-diligence.md` 与 `google-patents-search` 的核验协议，由原文逐字定位后人工确定。

## 何时调用

对每一件已经过检索式召回、准备进入创造性比对的文献调用一次。产品层文献先确认标题或摘要含有「石墨烯」等材料词，这一步由脚本用字符串完成。机制层文献不要求材料词出现在标题里。

不要把未公开的整份说明书或全部权利要求送给接口。一次只送目标句、最多 6 个特征，以及一篇文献的标题、摘要或一段已定位原文。

## 命令

```powershell
D:/Python/Python314/python.exe D:/aicoding/mylib/paa/skills/patent-jev-screen/scripts/screen.py --input <packet.json>
```

自检不访问网络：

```powershell
D:/Python/Python314/python.exe D:/aicoding/mylib/paa/skills/patent-jev-screen/scripts/screen.py --self-test
```

输入至少包含 `disclosure`（固定为 `public_prior_art`）、`lane`（`product` 或 `mechanism`）、`elements`、`candidate` 或最多 8 个 `candidates`。每个特征有 `id` 和 `text`。每篇文献有真实 `pub_number`、`title`、`abstract`、`passage` 和 `source_level`（`abstract` 或 `original_passage`）。

## 如何读结果

脚本对每个特征问一道是非题，并另问「是否全部特征都被写出」以及「下一步读原文、人看，还是停止」。问题和合成门槛写在 `scripts/screen.py` 顶部。`suggested_route` 只决定动作：

- `stop`：不下载、不写入对比文件；
- `human_review`：人看摘要或段落，不自动下载；
- `fetch_original`：摘要已经靠近目标句，取 PDF 或原文后再跑一遍，`source_level` 改为 `original_passage`；
- `map_passage`：原文段落值得逐特征填表。

`legal_conclusion` 恒为空。`map_passage` 之后由人把句子定位到权利要求或说明书段落，再按核验协议标 X、Y 或 A。概率高不是 X 类文件。任一特征在原文中找不到，就不能标成单独破坏新颖性的文件。

JEV 不可用时照实写明，并按已取到的原文继续。不得把接口失败写成「未发现现有技术」。

## 与独创性研判的衔接

特征句来自创造性锚点，也就是独权里仍可能被一篇文献打中的那几句，而不是发明名称。充分公开所缺的系数和阈值不放进这张表。评分器把本技能的路由当作证据去留，不把概率写入 AHP，也不把它当成授权概率。
