# Playbooks — 电网论文 × Codex × ARS

## A. 新开一篇电网/AI 稿

1. 工作区：打开 `D:/aicoding/powergrid_benchmark`（或具体 `paper_projects/<name>`）。
2. 读规则：项目 `AGENTS.md` + 目标刊 `Paper_CCF/journals/<slug>/SKILL.md`。
3. 收敛问题：
   ```text
   Use $academic-research-suite.
   主题：……；先苏格拉底式收敛研究问题与方法，不要写正文。
   ```
4. 本地证据：先看 `powergrid_paper/metadata/` 与 IdeaSpark / RepLLM-CPA 蒸馏，再写 related work。

## B. 文献综述（有本地语料）

1. Context：`papers/literature/`、`powergrid_paper/metadata/ideaspark_*`、`repllm_cpa_*`。
2. Constraints：优先本地 PDF / 蒸馏笔记；新增网搜引用必须可核验。
3. Call：`ars-lit-review` 或 `$academic-research-suite` + 主题。
4. Done when：空白点 / 争议点 / 已被充分研究者分栏，且每条能指回文件。

## C. 初稿 → 目标刊打磨

1. `Paper_CCF` 定期刊 fit（APC / soundness / section）。
2. `$academic-research-suite` → `academic-paper` revision / outline。
3. 闸门：`AERS-powergrid-bridge` → citation-checker + figure-table-audit + de-AIGC。
4. 可选：`ars-citation-check` 再跑一轮。
5. 摘要两轮"陌生读者"诊断（来自 `digests/submission-checkpoints-2026-09.md`）：第一轮只给摘要让 AI 复述"未知什么/做了什么/发现什么"；第二轮补引言问题段与结果发现段，对照过头/漏写/不一致；材料外信息列"待作者补充"，不许从材料外补结论。

## D. 投稿前审稿模拟

```text
Use $academic-research-suite.
请以期刊审稿人审阅 drafts/...（或 paper_projects/.../paper.tex）。
重点：问题是否清楚、方法能否回答、证据是否支撑、引用是否错配、desk-reject 风险。
直接说问题，不要夸。目标刊：Applied Sciences / CMC / Energies（选一）。
```

## E. 不该用 ARS 的时候

- 只下数据集 / 跑 aria2 → 用现有 `AGENTS.md` 下载规则与 `download_tools`。
- 只改期刊模板字体 → `Paper_CCF` / CMC style。
- 只做本地语料蒸馏 → IdeaSpark / RepLLM 脚本。

## F. 长稿 → 目标刊升级（瘦身 + 图表预算 + 补充材料迁移）

案例全量经验：`digests/mdpi-information-upgrade-2026-09.md`（MA-SQLGrid，42→30→31 页）。

1. 目标刊画像先读 `Paper_CCF/journals/<slug>/SKILL.md` + `references/standards-and-evidence.md`，确认正式篇幅口径与同刊实测页数带。
2. 量当前稿（页数、显示清单、孤儿图、末页余量、哈希）：
   ```text
   python -B D:/aicoding/mylib/Codex-Academic-Research/tools/manuscript_display_audit.py \
     --project <paper_dir> --tex paper.tex --figure-root figures
   ```
3. 与**同域最强对照件**比显示密度（(图+表)/页），不是与期刊均值比。低于对照件时三选一：合图回迁 / 图替表 / 去表留数。
4. 压缩原则：**迁移不删除**。表、图分列登记搬迁清单；收尾必查"包内每个图文件都被引用"与"补充材料 md ↔ PDF 双源一致"。
5. 页数决策先看工具输出的末页 headroom：余量 < 12 pt 时任何净增显示都会多一页，要先把账算清再删正文。
6. 图表可读性三查（display audit 不覆盖，需单独做）：渲染到目标刊栏宽（MDPI 单栏 ≈8.3 cm）的缩放图看字号/坐标轴；灰度转换后看数据组区分度；图注脱离正文独读是否自足（研究对象、缩写、误差线/样本量）。三查通过才进包。
7. 搬迁后必须重跑：编译门禁、包内内容断言、`fresh_extract`、投稿包/审阅包隔离。

## G. 新实验是否写进已有稿（预声明判据）

案例：`PAPER_UPDATE_CRITERIA_20260921.md`（看结果之前写判据）→ `PAPER_UPDATE_DECISION_20260922.md`（逐条判定）。

1. 在读取新结果**之前**写判据文件：C1 新可复核证据 / C2 是否改变现有论断 / C3 是否回应评审共同缺口 / C4 过度声称风险 / C5 是否与历史数字冲突 / C6 重建成本 / C7 追问抵御力，外加可判定的阈值（本例 T1 ≥6/8 库同向、T2 率值 ≥25% 且双骨干重复）。
2. 结果出来后逐条判定，写成决策文件；达标才进正文受限小节，不达标降级为次级观察或补充材料。
3. **摘要级主张不动**；把"不得声称"清单直接写进 Limitations，并同步更新包与校验件。

## H. 投稿日与投稿后（清单 + 一致性 + 状态跟踪）

蒸馏自 `digests/submission-checkpoints-2026-09.md`；文件级完整性用 fail-closed 门禁与哈希包（不回退到手工清单），本节补的是**元数据与人因**层。

1. `投稿前材料清单.md`：按目标刊指南逐项（作者信息、伦理/COI、数据可用性、作者贡献、推荐审稿人、参考文献）写"指南要求—材料现状—所在文件"，缺的列待补，不替作者填。
2. `投稿材料一致性检查.md`：封面信 / 标题页 / 系统字段三方比对（标题、作者顺序与单位、通讯邮箱、数据链接）；**只列差异，不判定哪份正确**，逐项请作者确认。教训锚点：C2GES 曾把"通讯邮箱未改"留成手工项。
3. `投稿状态记录.md`：投稿后第 2/4/6 天查系统，每周查投稿邮箱+垃圾邮件（CronCreate 定时提醒）；记状态、补件要求、回复期限、下一步；有决定后停止提醒。

## I. 拒稿处置（先拆解，后选路）

1. 先判类型：编辑初筛（重看期刊范围与定位）还是外审后拒（逐条评估可修性）；引用决定信原句支撑判断。
2. `拒稿意见拆解.md`：每条意见 → 稿件位置 → 归类（范围/证据/写作/格式）→ 可能动作（改文字/补材料/增分析/请作者判断）。**不把建议写成已完成的工作**。
3. 作者选定路线（修订重投 / 转投 / 申诉）后再写 `下一步投稿计划.md`；转投时重新核对目标刊范围、格式、材料；申诉按"决定信依据—稿件事实—请求事项"三段写给编辑。
4. **决定信当晚不把未改原稿投下一家。**

## J. 诊断 / 负结果评测（配对差、零膨胀、界值）

蒸馏自 C²GES（Information 2026-09 轮）：`digests/powergrid-diagnostic-eval-2026-09.md`；
工具：`tools/paired_diagnostic_stats.py`（纯标准库，`--self-test` 复现已发表数字）。

触发语：**"某组件没带来增益"**、负结果论文、消融全零、审稿人说"你的零结果没有信息量"。

1. 先查四个统计陷阱：**预算混淆**（等句数 ≠ 等词，赢家可能只是输出更长）、**零膨胀**（同池换权重 → 大量精确 0）、**重尾**（一篇文档支配均值）、**功效天花板**（n=7 在 Holm 下即使 7/7 同号也过不了 0.05：`k·2/2ⁿ`）。
2. **把零结果写成界**：给每个预算/对比算单侧 95% bootstrap **上界** + **留一法**最坏上界；把主判据从上界出发，而不是从"p>0.05"出发。事后界必须标注 post hoc（正文、表注、回复信三处）。
3. 任何"某方法更好"都必须绑定**预算类型**；排序随预算翻转是常态，不是噪声。
4. 每个对比必报：n、零质量、不一致对（负/正/平）、符号占比、效应量与区间；均值要在留一法下能被引用才写进摘要。
5. 新语料入稿前先冻结协议（语料清单 + 抽样种子 + 单元规则 + 臂集合 + 预算 + 端点 + 判据 + 判定表），带哈希留档；"扩展/敏感性"层永不写成 confirmatory。
6. 跨域层要显式声明"该层不能说明什么"（如域内线索词表跨域后只能界定风险）；不与域内层合并统计。
7. 收尾门禁：逐层验证组（把正文数字绑回数据文件）+ 逐字文本闸门（已发布数据记录不得含 ≥300 字符且 ≥40 词的连续散文）+ 浮动体闸门（shipped tex 的每个 `\includegraphics` 必须在包内）+ 派生表闸门（写表脚本拒绝 >400 字符字段）。
8. 补充表**由数据文件生成**（marker 区域内替换），不手抄数字；改完最后一处文字后重跑：编译 → 包 → 公共验证 → 清单 `--check`。
