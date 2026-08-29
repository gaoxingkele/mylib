---
name: Paper_CCF
description: Use when writing, targeting, or choosing the venue for a computer-science / engineering paper — CONFERENCES (155 CS venues) AND selected JOURNALS (29 profiles: IEEE Access/IoT-J, MDPI Energies/Electronics/Information/Algorithms/Remote Sensing/…, CMC, Discover Computing, PeerJ CS, Journal of Energy Storage, Scientific Reports, …). Give a venue name or acronym and it loads that venue's fit / evidence-bar / APC & review model / submission-cycle / desk-reject / re-routing profile.
---

# Paper_CCF — 计算机会议投稿路由器 (CS / CCF conferences)

按**venue 名称或缩写自动定位**到对应会场的“内涵”（定位、方法与证据标准、官方周期清单、desk-reject 触发点、改投建议、输出格式）。本 skill 有两个模块：

- **会议模块（155 个 CS 顶会/主流会议）** —— 画像在 `skills/<slug>/SKILL.md`，索引见下方「会议索引（155）」。
- **期刊模块（29 本工程/CS/能源相关期刊）** —— 画像在 `journals/<slug>/SKILL.md`，索引见下方「期刊索引」（含 IEEE Access/IoT-J、MDPI 多刊、CMC、Discover Computing、PeerJ CS、J. Energy Storage 等）。

先判断用户目标是**会议**还是**期刊**，再进对应模块路由。

> **代码级调用（其他项目可用）**：会议+期刊的结构化数据导出在 `data/venues.json`，配零依赖读取器 `data/paper_ccf.py`（`find()/get()/fastest()/to_paper_reviews()`）。其他项目（如 paper_reviews）可按全局路径 `~/.claude/skills/Paper_CCF/data/` 读取；改了画像后跑 `py data/build_venues.py` 重新导出。详见 `data/README.md`。

> 会议 vs 期刊的“内核”不同：**会议**没有常任主编、逐年轮换 Program/General Chairs、无 APC（成本＝注册费+开放论文集）、按 DDL 成批评审、看重 novelty。**期刊**有主编/编委与 Guest Editor、滚动投稿、收 APC、按 soundness（尤其 IEEE Access/MDPI）评审、有 IF/分区/Special Issue。别把两套规则混用。

## 使用方法（路由步骤）

1. **确定目标会议**：从用户处拿到会议缩写（如 `NeurIPS` / `CVPR` / `S&P` / `KDD` / `ICSE`）或全名。
2. **查索引定位 slug**：在下方「会议索引（155）」按缩写或全名找到该会议的 `slug`。
3. **加载该会议画像**：打开 `skills/<slug>/SKILL.md`，据其 fit / 证据标准 / 官方周期清单 / desk-reject / 改投 / 输出格式 给出建议。
4. **会议不明或需在兄弟会议间取舍**：打开 `skills/cs-ai-conference-workflow/SKILL.md`（按贡献类型的分区路由表 + 兄弟会议辨析），并参考 `resources/exemplars/selection-patterns.md` 与 `resources/worked-examples/venue-routing.md`。
5. **投稿前务必核对官方当年规则**：会议每届的 DDL、页数、模板、双盲、rebuttal、artifact、AI 使用政策都会变。用 `resources/conference-roster.md` 与 `resources/official-source-map.md` 找到官方 CFP / author kit 链接，以官方为准；官方与本 skill 冲突时以官方为准。

## 期刊模块（Journals）路由

若用户目标是**期刊**（问某本 OA 期刊，或“投哪个 OA 期刊 / 版面费 / 影响因子 / 审稿多快 / Special Issue / 电力+CS 发哪”）：

1. 在下方「期刊索引（15）」按名称找到 `slug`，打开 `journals/<slug>/SKILL.md`：该刊的 fit / 证据标准（多为 **soundness 而非 novelty**）/ APC 与开放获取 / 评审模型与时长 / Special Issue 动态 / desk-reject / 改投 / 输出格式。
2. **要在多本间“按审稿速度 / 电力×CS 契合度 / 成本”排序选刊** → 直接读 `resources/journal-selection-guide.md`（对照总表 + 决策口诀 + 避坑 + **电力开放数据语料蒸馏**）。
3. MDPI 各刊先读共性说明 `resources/mdpi-common.md`（SuSy 投稿、单盲快审、Section+Special Issue、APC 录用后收取、house style、声誉说明）。
4. **电力系统公开数据集 × OA 投稿经验**（本地 90 篇去重 PDF 蒸馏）→ `resources/powergrid-open-data-corpus-distill.md`；各刊 `journals/<slug>/SKILL.md` 内已有对应 “Supplement / Distilled patterns” 小节。
5. **2026-08 目标刊扩展批次**（CMC 等 14 本新画像 + CMC 本地 10 篇全文蒸馏）→ `resources/target-journals-2026-batch-distill.md`。
6. **IdeaSpark 全量本地语料蒸馏**（`papers/literature/**` ≈480 PDF → 按刊 acceptance pattern）→ **先读** `resources/ideaspark-fullcorpus-journal-distill.md`；各命中刊 `journals/<slug>/SKILL.md` 内有 `### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)`。细表/卡片在仓库 `papers/literature/target_journal_related/metadata/ideaspark_fullcorpus_*`。
7. **RepLLM-CPA 结构化证据蒸馏**（Content Parsing → `paper.json`，**非**全量代码复现）→ `resources/repllm-cpa-journal-distill.md`；各刊 `### RepLLM-CPA structured evidence`。库：`D:/aicoding/mylib/RepLLM/`。
8. **所有 IF / 分区 / APC / 审稿时长均为快照，逐年变动——务必以官网/Clarivate 当年数据为准**；官网与本 skill 冲突以官网为准。总索引见 `resources/journal-roster.md`。

### 期刊索引（29）

**A. 广谱工程/CS OA**
| 期刊 | 关键内核 | 速度 · IF · APC（快照，需核对） | slug |
|---|---|---|---|
| IEEE Access | **只看 soundness**；**二元 Accept/Reject**；IEEE 品牌 | ~4 周首决 · IF≈4.2 Q2 · US$2,160 | `ieee-access` |
| MDPI Electronics | 应用 EE/CS，重严谨；~16 Sections | ~15 天首决 · IF≈2.9 Q2 · CHF 2,400 | `mdpi-electronics` |
| MDPI Applied Sciences | 极广应用科学/工程，重应用轻理论；~32 Sections | ~15 天首决 · IF≈2.9 ~Q2 · CHF 2,400 | `mdpi-applied-sciences` |
| MDPI Information | 信息科学/知识/数据/应用 AI | ~19 天 · IF≈4.3 Q2 · CHF 1,800 | `mdpi-information` |
| MDPI Algorithms | **算法本身**须为核心 | ~18 天 · IF≈2.6 Q2 · CHF 1,800 | `mdpi-algorithms` |
| MDPI Future Internet | Internet/IoT 网络架构须为核心 | ~15 天 · IF≈4.6 Q2 · CHF 1,800 | `mdpi-future-internet` |
| CMC (TSP) | 应用 CS/AI/材料信息；中档 SCIE | 数周–数月 · IF≈2.4 · US$1,600 | `tsp-cmc` |
| Discover Computing | SN Discover 广谱 CS soundness OA | 中等 · IF≈1.9 · 折扣 APC 至2026-12 | `springer-discover-computing` |
| PeerJ Computer Science | 发展式审稿；APC 或终身会员 | 中等 · APC≈US$2,155 | `peerj-computer-science` |
| IJACSA (SAI) | 低–中档 CS OA；声誉需自审 | 快 · ESCI IF≈1.1 · ~£800 | `ijacsa` |

**B. 电力 / 能源 / 储能**
| 期刊 | 关键内核 | 速度 · IF · APC（需核对） | slug |
|---|---|---|---|
| **PCMP** | **免费(钻石OA)+最快+最高IF**；限**保护/控制/故障/稳定** | **~4 周** · IF≈11.9 **Q1** · **免费** | `pcmp` |
| CSEE JPES | 广 smart grid/数据驱动电力；学会+IEEE Xplore；Q1 | ~2–3 月首决 · IF≈5.9 **Q1** · 2026起 CNY800/USD120 每页 | `csee-jpes` |
| OAJPE | IEEE PES 品牌电力 OA | 未公布(~10周见刊) · IF≈2.8 Q1(Scimago) · US$2,160 | `ieee-oajpe` |
| MDPI Energies | 广义能源/电力系统 + 明确应用 | ~16 天首决 · IF≈4.0 Q2 · CHF 2,600 | `mdpi-energies` |
| Energy Reports | Elsevier；AI-for-energy；Q1（有诚信争议） | 见刊~16 周 · IF≈6.3+ **Q1** · ~US$3,040 | `elsevier-energy-reports` |
| Frontiers Energy Research | 互动式评审(具名)；走 Smart Grids 分区 | 评审<90天 · IF≈2.58 Q2 · CHF 2,695 | `frontiers-energy-research` |
| Journal of Energy Storage | **储能须为核心**；高 IF 选择性 hybrid | 数周首决 · IF≈10 **Q1** · OA≈US$3.7k | `elsevier-journal-of-energy-storage` |
| Unconventional Resources | 非常规油气/地质能源（电网 CS 通常不匹配） | 季刊 · APC 至2026-04前免 / 后 US$700 | `keai-unconventional-resources` |

**C. 对口子领域（传感 / 机器 / 数学 / 可持续 / 遥感 / 大气 / 对称 / IoT）**
| 期刊 | 关键内核（须对口才收） | 速度 · IF · APC（需核对） | slug |
|---|---|---|---|
| MDPI Sensors | 传感/测量须为核心（电网监测/PMU/IoT） | ~18 天首决 · IF≈3.5 Q2 · CHF 2,600 | `mdpi-sensors` |
| MDPI Machines | 具体电机/驱动/控制系统 | ~16 天首决 · IF≈2.5 · CHF 2,400 | `mdpi-machines` |
| MDPI Mathematics | 需真正数学新意（优化/ML 理论） | ~17 天首决 · IF≈2.3 **Q1** · CHF 2,600 | `mdpi-mathematics` |
| MDPI Sustainability | 需实质可持续/SDG 角度 | ~17 天首决 · IF≈3.3 Q2 · CHF 2,400 | `mdpi-sustainability` |
| MDPI Remote Sensing | **遥感/EO 须为核心**（辐照/走廊监测） | ~24 天 · IF≈4.1 **Q1** · CHF 2,700 | `mdpi-remote-sensing` |
| MDPI Atmosphere | **大气科学须为核心** | ~20 天 · IF≈2.6 · CHF 2,400 | `mdpi-atmosphere` |
| MDPI Symmetry | **对称/不对称须为真贡献** | ~16 天 · IF≈2.2 · CHF 2,400 | `mdpi-symmetry` |
| IEEE IoT Journal | 选择性 IoT 系统；高 IF hybrid | ~7 周首决 · IF≈8.7 **Q1** · OA≈US$2,695+超页 | `ieee-internet-of-things-journal` |
| CCPE (Wiley) | 并行/分布式/并发实践 | hybrid · IF~1.5 / CS~5 · 核对 OA | `wiley-ccpe` |

**D. 广谱兜底 OA（改投/跨学科）**
| 期刊 | 关键内核 | 速度 · IF · APC（需核对） | slug |
|---|---|---|---|
| Scientific Reports | Nature 系；soundness 不看 novelty；稳定收录 | **不快(~4–6 月)** · IF≈3.8 **Q1** · US$2,850 | `nature-scientific-reports` |
| Heliyon | Cell Press；有 Eng/CS 分区；便宜 | 中等 · IF≈3.4 · US$1,950 · ⚠️**WoS 自2024暂停收录，投前必查** | `elsevier-heliyon` |

**会议 vs 期刊 / 快速口诀**：严谨但新意一般 + 想快 OA → IEEE Access / MDPI（~15天–4周）/ CMC；有保护控制角度 + 想免费最快 → **PCMP**；广 smart grid + Q1 → **CSEE JPES**；储能核心 → **J. Energy Storage**；IoT 系统高 IF → **IEEE IoT-J**；AI-for-energy + Q1 → Energy Reports / Energies；novelty 驱动 → 会议模块或选择性 IEEE Transactions。完整排序见 `resources/journal-selection-guide.md`。

## 路由前先问六件事

1. **贡献类型**：算法 / 理论 / 系统 / 数据集 / benchmark / 实证研究 / 用户研究 / 安全发现 / 编程语言结果 / 数据库系统 / 应用。
2. **证据形态**：证明 / benchmark / 消融 / artifact / 部署 / 用户研究 / 现场研究 / 攻防 / 定理 / 系统测量。
3. **受众**：广义 AI / 子领域专家 / 系统构建者 / 安全审稿人 / HCI 设计研究者 / 理论社区 / 领域用户。
4. **评审约束**：双盲/匿名、OpenReview 可见性、rebuttal 长度、artifact 政策、伦理、AI 使用披露、补充材料规则。
5. **周期风险**：DDL、页数上限、作者注册、利益冲突声明、dual-submission 政策、camera-ready 义务。
6. **备选路径**：兄弟会议、期刊、workshop、findings track、或仅 arXiv 修订。

## 决策规则（要点；完整启发式见 `skills/cs-ai-conference-workflow/SKILL.md`）

- **AI 优先**：若本质是机器学习/语言/视觉/数据挖掘/智能体/负责任 AI，先在 AI/ML 分区里选，再考虑通用 CS 会场。
- **贡献类型压过名气**：定理→COLT/STOC/FOCS/LICS 类；系统→SOSP/OSDI/NSDI/SIGCOMM/ASPLOS 类；面向用户的 AI 界面→CHI/IUI/CSCW 而非只投 NeurIPS。
- **证据必须匹配会场文化**：顶级 AI 要强 baseline + 消融；系统要 artifact + workload；安全要威胁模型 + 伦理；HCI 要研究设计 + 被试语境；理论要完整证明。
- **官方周期易变**：给出可提交建议前，务必打开该会议单会画像并核对当年 CFP/author kit。
- **rebuttal 姿态**：简洁、以证据为据；作者回复阶段不得泄露身份或新增违规材料。

## 会议索引（155）

按 `resources/conference-roster.md` 排序（AI/ML 优先）。列：缩写 · 全名 · 领域 · slug（对应 `skills/<slug>/SKILL.md`）。

| 缩写 / Acronym | 会议全名 / Venue | 领域 / Area | slug |
|---|---|---|---|
| NeurIPS | Conference on Neural Information Processing Systems | AI/ML flagship | `neural-information-processing-systems` |
| ICML | International Conference on Machine Learning | AI/ML flagship | `international-conference-on-machine-learning` |
| ICLR | International Conference on Learning Representations | AI/ML flagship | `international-conference-on-learning-representations` |
| AAAI | AAAI Conference on Artificial Intelligence | AI/ML flagship | `aaai-conference-on-artificial-intelligence` |
| IJCAI | International Joint Conference on Artificial Intelligence | AI/ML flagship | `international-joint-conference-on-artificial-intelligence` |
| AISTATS | International Conference on Artificial Intelligence and Statistics | AI statistics | `artificial-intelligence-and-statistics` |
| UAI | Conference on Uncertainty in Artificial Intelligence | AI statistics | `uncertainty-in-artificial-intelligence` |
| COLT | Conference on Learning Theory | learning theory | `conference-on-learning-theory` |
| MLSys | Conference on Machine Learning and Systems | ML systems | `conference-on-machine-learning-and-systems` |
| CoLLAs | Conference on Lifelong Learning Agents | continual learning | `conference-on-lifelong-learning-agents` |
| AutoML Conference | International Conference on Automated Machine Learning | automated ML | `international-conference-on-automated-machine-learning` |
| CHIL | Conference on Health, Inference, and Learning | AI for health | `conference-on-health-inference-and-learning` |
| ML4H | Machine Learning for Health | AI for health | `machine-learning-for-health` |
| KDD | ACM SIGKDD Conference on Knowledge Discovery and Data Mining | data mining | `acm-sigkdd-conference-on-knowledge-discovery-and-data-mining` |
| ICDM | IEEE International Conference on Data Mining | data mining | `ieee-international-conference-on-data-mining` |
| SDM | SIAM International Conference on Data Mining | data mining | `siam-international-conference-on-data-mining` |
| ECML PKDD | European Conference on Machine Learning and Principles and Practice of Knowledge Discovery in Databases | AI/data mining | `european-conference-on-machine-learning-and-principles-and-practice-of-knowledge-discovery` |
| ACML | Asian Conference on Machine Learning | AI/ML regional flagship | `asian-conference-on-machine-learning` |
| Discovery Science | International Conference on Discovery Science | discovery science | `international-conference-on-discovery-science` |
| RecSys | ACM Conference on Recommender Systems | recommender systems | `acm-conference-on-recommender-systems` |
| WWW | The Web Conference | web and AI | `the-web-conference` |
| WSDM | ACM International Conference on Web Search and Data Mining | web search and mining | `acm-international-conference-on-web-search-and-data-mining` |
| CIKM | ACM International Conference on Information and Knowledge Management | information and knowledge management | `acm-international-conference-on-information-and-knowledge-management` |
| ISWC | International Semantic Web Conference | semantic web | `international-semantic-web-conference` |
| K-CAP | International Conference on Knowledge Capture | knowledge capture | `international-conference-on-knowledge-capture` |
| ICAPS | International Conference on Automated Planning and Scheduling | planning and scheduling | `international-conference-on-automated-planning-and-scheduling` |
| KR | International Conference on Principles of Knowledge Representation and Reasoning | knowledge representation | `international-conference-on-principles-of-knowledge-representation-and-reasoning` |
| AAMAS | International Conference on Autonomous Agents and Multiagent Systems | agents and multiagent systems | `international-conference-on-autonomous-agents-and-multiagent-systems` |
| CP | International Conference on Principles and Practice of Constraint Programming | constraints | `international-conference-on-principles-and-practice-of-constraint-programming` |
| SAT | International Conference on Theory and Applications of Satisfiability Testing | satisfiability | `international-conference-on-theory-and-applications-of-satisfiability-testing` |
| CPAIOR | Integration of Constraint Programming, Artificial Intelligence, and Operations Research | AI/OR optimization | `integration-of-constraint-programming-artificial-intelligence-and-operations-research` |
| AIES | AAAI/ACM Conference on AI, Ethics, and Society | AI ethics and society | `aaai-acm-conference-on-ai-ethics-and-society` |
| FAccT | ACM Conference on Fairness, Accountability, and Transparency | responsible AI | `acm-conference-on-fairness-accountability-and-transparency` |
| HCOMP | AAAI Conference on Human Computation and Crowdsourcing | human computation | `aaai-conference-on-human-computation-and-crowdsourcing` |
| ECAI | European Conference on Artificial Intelligence | AI/ML regional flagship | `european-conference-on-artificial-intelligence` |
| CVPR | IEEE/CVF Conference on Computer Vision and Pattern Recognition | computer vision flagship | `computer-vision-and-pattern-recognition` |
| ICCV | IEEE/CVF International Conference on Computer Vision | computer vision flagship | `international-conference-on-computer-vision` |
| ECCV | European Conference on Computer Vision | computer vision flagship | `european-conference-on-computer-vision` |
| WACV | IEEE/CVF Winter Conference on Applications of Computer Vision | computer vision applications | `winter-conference-on-applications-of-computer-vision` |
| ACCV | Asian Conference on Computer Vision | computer vision regional flagship | `asian-conference-on-computer-vision` |
| BMVC | British Machine Vision Conference | computer vision | `british-machine-vision-conference` |
| ICPR | International Conference on Pattern Recognition | pattern recognition | `international-conference-on-pattern-recognition` |
| 3DV | International Conference on 3D Vision | 3D vision | `international-conference-on-3d-vision` |
| MICCAI | International Conference on Medical Image Computing and Computer Assisted Intervention | medical imaging AI | `medical-image-computing-and-computer-assisted-intervention` |
| ISBI | IEEE International Symposium on Biomedical Imaging | biomedical imaging | `ieee-international-symposium-on-biomedical-imaging` |
| ACM MM | ACM International Conference on Multimedia | multimedia | `acm-international-conference-on-multimedia` |
| ICMR | ACM International Conference on Multimedia Retrieval | multimedia retrieval | `acm-international-conference-on-multimedia-retrieval` |
| SIGGRAPH | ACM SIGGRAPH | computer graphics flagship | `acm-siggraph` |
| SIGGRAPH Asia | ACM SIGGRAPH Asia | computer graphics flagship | `acm-siggraph-asia` |
| Eurographics | Eurographics Annual Conference | computer graphics | `eurographics` |
| SCA | ACM SIGGRAPH/Eurographics Symposium on Computer Animation | computer animation | `acm-siggraph-eurographics-symposium-on-computer-animation` |
| ISMAR | IEEE International Symposium on Mixed and Augmented Reality | mixed and augmented reality | `ieee-international-symposium-on-mixed-and-augmented-reality` |
| IEEE VR | IEEE Conference on Virtual Reality and 3D User Interfaces | virtual reality | `ieee-conference-on-virtual-reality-and-3d-user-interfaces` |
| Pacific Graphics | Pacific Graphics | computer graphics | `pacific-graphics` |
| I3D | ACM SIGGRAPH Symposium on Interactive 3D Graphics and Games | interactive graphics | `acm-siggraph-symposium-on-interactive-3d-graphics-and-games` |
| ACL | Annual Meeting of the Association for Computational Linguistics | NLP flagship | `annual-meeting-of-the-association-for-computational-linguistics` |
| EMNLP | Conference on Empirical Methods in Natural Language Processing | NLP flagship | `conference-on-empirical-methods-in-natural-language-processing` |
| NAACL | Annual Conference of the North American Chapter of the Association for Computational Linguistics | NLP regional flagship | `north-american-chapter-of-the-association-for-computational-linguistics` |
| EACL | Conference of the European Chapter of the Association for Computational Linguistics | NLP regional flagship | `european-chapter-of-the-association-for-computational-linguistics` |
| COLING | International Conference on Computational Linguistics | computational linguistics | `international-conference-on-computational-linguistics` |
| CoNLL | Conference on Computational Natural Language Learning | NLP learning | `conference-on-computational-natural-language-learning` |
| INLG | International Natural Language Generation Conference | language generation | `international-natural-language-generation-conference` |
| SIGDIAL | SIGDIAL Conference on Discourse and Dialogue | dialogue systems | `sigdial-conference-on-discourse-and-dialogue` |
| LREC-COLING | Joint International Conference on Computational Linguistics, Language Resources and Evaluation | language resources | `joint-international-conference-on-computational-linguistics-language-resources-and-evaluation` |
| *SEM | StarSem Conference on Computational Semantics | computational semantics | `starsem-conference-on-computational-semantics` |
| INTERSPEECH | INTERSPEECH | speech processing | `interspeech` |
| ICASSP | IEEE International Conference on Acoustics, Speech and Signal Processing | signal processing | `ieee-international-conference-on-acoustics-speech-and-signal-processing` |
| ASRU | IEEE Automatic Speech Recognition and Understanding Workshop | speech recognition | `ieee-automatic-speech-recognition-and-understanding-workshop` |
| SLT | IEEE Spoken Language Technology Workshop | spoken language technology | `ieee-spoken-language-technology-workshop` |
| SIGIR | ACM SIGIR Conference on Research and Development in Information Retrieval | information retrieval flagship | `acm-sigir-conference-on-research-and-development-in-information-retrieval` |
| ECIR | European Conference on Information Retrieval | information retrieval | `european-conference-on-information-retrieval` |
| CHIIR | ACM SIGIR Conference on Human Information Interaction and Retrieval | interactive IR | `acm-sigir-conference-on-human-information-interaction-and-retrieval` |
| JCDL | ACM/IEEE Joint Conference on Digital Libraries | digital libraries | `acm-ieee-joint-conference-on-digital-libraries` |
| CLEF | Conference and Labs of the Evaluation Forum | evaluation forum | `conference-and-labs-of-the-evaluation-forum` |
| TREC | Text REtrieval Conference | retrieval evaluation | `text-retrieval-conference` |
| ICRA | IEEE International Conference on Robotics and Automation | robotics flagship | `ieee-international-conference-on-robotics-and-automation` |
| IROS | IEEE/RSJ International Conference on Intelligent Robots and Systems | robotics flagship | `ieee-rsj-international-conference-on-intelligent-robots-and-systems` |
| RSS | Robotics: Science and Systems | robotics flagship | `robotics-science-and-systems` |
| CoRL | Conference on Robot Learning | robot learning | `conference-on-robot-learning` |
| HRI | ACM/IEEE International Conference on Human-Robot Interaction | human-robot interaction | `acm-ieee-international-conference-on-human-robot-interaction` |
| RO-MAN | IEEE International Conference on Robot and Human Interactive Communication | human-robot communication | `ieee-international-conference-on-robot-and-human-interactive-communication` |
| CASE | IEEE International Conference on Automation Science and Engineering | automation | `ieee-international-conference-on-automation-science-and-engineering` |
| ISRR | International Symposium on Robotics Research | robotics research | `international-symposium-on-robotics-research` |
| ISER | International Symposium on Experimental Robotics | experimental robotics | `international-symposium-on-experimental-robotics` |
| RoboCup | RoboCup Symposium | robotics competitions | `robocup` |
| Humanoids | IEEE-RAS International Conference on Humanoid Robots | humanoid robotics | `ieee-ras-international-conference-on-humanoid-robots` |
| DARS | International Symposium on Distributed Autonomous Robotic Systems | multi-robot systems | `international-symposium-on-distributed-autonomous-robotic-systems` |
| CHI | ACM CHI Conference on Human Factors in Computing Systems | HCI flagship | `acm-chi-conference-on-human-factors-in-computing-systems` |
| UIST | ACM Symposium on User Interface Software and Technology | UI systems | `acm-symposium-on-user-interface-software-and-technology` |
| CSCW | ACM Conference on Computer-Supported Cooperative Work and Social Computing | social computing | `acm-conference-on-computer-supported-cooperative-work-and-social-computing` |
| DIS | ACM Conference on Designing Interactive Systems | interaction design | `acm-conference-on-designing-interactive-systems` |
| IUI | ACM Conference on Intelligent User Interfaces | intelligent interfaces | `acm-conference-on-intelligent-user-interfaces` |
| UbiComp | ACM International Joint Conference on Pervasive and Ubiquitous Computing | ubiquitous computing | `acm-international-joint-conference-on-pervasive-and-ubiquitous-computing` |
| MobileHCI | ACM International Conference on Mobile Human-Computer Interaction | mobile HCI | `acm-international-conference-on-mobile-human-computer-interaction` |
| TEI | ACM International Conference on Tangible, Embedded, and Embodied Interaction | tangible interaction | `acm-international-conference-on-tangible-embedded-and-embodied-interaction` |
| ASSETS | ACM SIGACCESS Conference on Computers and Accessibility | accessibility | `acm-sigaccess-conference-on-computers-and-accessibility` |
| AVI | International Conference on Advanced Visual Interfaces | visual interfaces | `international-conference-on-advanced-visual-interfaces` |
| IEEE VIS | IEEE Visualization Conference | visualization flagship | `ieee-visualization-conference` |
| EuroVis | EuroVis | visualization | `eurovis` |
| PacificVis | IEEE Pacific Visualization Symposium | visualization | `ieee-pacific-visualization-symposium` |
| ISS | ACM Interactive Surfaces and Spaces | interactive surfaces | `acm-interactive-surfaces-and-spaces` |
| VRST | ACM Symposium on Virtual Reality Software and Technology | VR software | `acm-symposium-on-virtual-reality-software-and-technology` |
| SOSP | ACM Symposium on Operating Systems Principles | systems flagship | `acm-symposium-on-operating-systems-principles` |
| OSDI | USENIX Symposium on Operating Systems Design and Implementation | systems flagship | `usenix-symposium-on-operating-systems-design-and-implementation` |
| NSDI | USENIX Symposium on Networked Systems Design and Implementation | networked systems | `usenix-symposium-on-networked-systems-design-and-implementation` |
| SIGCOMM | ACM SIGCOMM | networking flagship | `acm-sigcomm` |
| MobiCom | ACM MobiCom | mobile networking | `acm-mobicom` |
| MobiSys | ACM MobiSys | mobile systems | `acm-mobisys` |
| CoNEXT | ACM CoNEXT | networking | `acm-conext` |
| INFOCOM | IEEE INFOCOM | networking | `ieee-infocom` |
| EuroSys | EuroSys | systems | `eurosys` |
| USENIX ATC | USENIX Annual Technical Conference | systems | `usenix-annual-technical-conference` |
| FAST | USENIX Conference on File and Storage Technologies | storage systems | `usenix-conference-on-file-and-storage-technologies` |
| ASPLOS | ACM International Conference on Architectural Support for Programming Languages and Operating Systems | architecture/systems/PL | `architectural-support-for-programming-languages-and-operating-systems` |
| ISCA | International Symposium on Computer Architecture | computer architecture flagship | `international-symposium-on-computer-architecture` |
| MICRO | IEEE/ACM International Symposium on Microarchitecture | microarchitecture flagship | `ieee-acm-international-symposium-on-microarchitecture` |
| HPCA | IEEE International Symposium on High-Performance Computer Architecture | computer architecture | `ieee-international-symposium-on-high-performance-computer-architecture` |
| SC | International Conference for High Performance Computing, Networking, Storage and Analysis | HPC flagship | `international-conference-for-high-performance-computing-networking-storage-and-analysis` |
| PPoPP | ACM SIGPLAN Symposium on Principles and Practice of Parallel Programming | parallel programming | `acm-sigplan-symposium-on-principles-and-practice-of-parallel-programming` |
| HPDC | ACM International Symposium on High-Performance Parallel and Distributed Computing | parallel/distributed computing | `acm-international-symposium-on-high-performance-parallel-and-distributed-computing` |
| SIGMETRICS | ACM SIGMETRICS | performance measurement | `acm-sigmetrics` |
| HotNets | ACM Workshop on Hot Topics in Networks | networking workshop | `acm-workshop-on-hot-topics-in-networks` |
| IEEE S&P | IEEE Symposium on Security and Privacy | security flagship | `ieee-symposium-on-security-and-privacy` |
| USENIX Security | USENIX Security Symposium | security flagship | `usenix-security-symposium` |
| CCS | ACM Conference on Computer and Communications Security | security flagship | `acm-conference-on-computer-and-communications-security` |
| NDSS | Network and Distributed System Security Symposium | security flagship | `network-and-distributed-system-security-symposium` |
| PETS | Privacy Enhancing Technologies Symposium | privacy | `privacy-enhancing-technologies-symposium` |
| RAID | International Symposium on Research in Attacks, Intrusions and Defenses | attacks and defenses | `international-symposium-on-research-in-attacks-intrusions-and-defenses` |
| ACSAC | Annual Computer Security Applications Conference | applied security | `annual-computer-security-applications-conference` |
| ESORICS | European Symposium on Research in Computer Security | security | `european-symposium-on-research-in-computer-security` |
| ASIACCS | ACM Asia Conference on Computer and Communications Security | security | `acm-asia-conference-on-computer-and-communications-security` |
| WiSec | ACM Conference on Security and Privacy in Wireless and Mobile Networks | wireless/mobile security | `acm-conference-on-security-and-privacy-in-wireless-and-mobile-networks` |
| CHES | IACR Conference on Cryptographic Hardware and Embedded Systems | crypto hardware | `iacr-conference-on-cryptographic-hardware-and-embedded-systems` |
| FC | Financial Cryptography and Data Security | financial security | `financial-cryptography-and-data-security` |
| ICSE | International Conference on Software Engineering | software engineering flagship | `international-conference-on-software-engineering` |
| FSE | ACM International Conference on the Foundations of Software Engineering | software engineering flagship | `acm-international-conference-on-the-foundations-of-software-engineering` |
| ASE | IEEE/ACM International Conference on Automated Software Engineering | automated software engineering | `ieee-acm-international-conference-on-automated-software-engineering` |
| ISSTA | ACM SIGSOFT International Symposium on Software Testing and Analysis | software testing | `acm-sigsoft-international-symposium-on-software-testing-and-analysis` |
| MSR | Mining Software Repositories | software analytics | `mining-software-repositories` |
| ICSME | IEEE International Conference on Software Maintenance and Evolution | software maintenance | `ieee-international-conference-on-software-maintenance-and-evolution` |
| SANER | IEEE International Conference on Software Analysis, Evolution and Reengineering | software analysis | `ieee-international-conference-on-software-analysis-evolution-and-reengineering` |
| ESEM | International Symposium on Empirical Software Engineering and Measurement | empirical software engineering | `international-symposium-on-empirical-software-engineering-and-measurement` |
| RE | IEEE International Requirements Engineering Conference | requirements engineering | `ieee-international-requirements-engineering-conference` |
| MODELS | ACM/IEEE International Conference on Model Driven Engineering Languages and Systems | model-driven engineering | `acm-ieee-international-conference-on-model-driven-engineering-languages-and-systems` |
| PLDI | ACM SIGPLAN Conference on Programming Language Design and Implementation | programming languages flagship | `acm-sigplan-conference-on-programming-language-design-and-implementation` |
| POPL | ACM SIGPLAN Symposium on Principles of Programming Languages | programming languages flagship | `acm-sigplan-symposium-on-principles-of-programming-languages` |
| OOPSLA | ACM SIGPLAN Conference on Object-Oriented Programming, Systems, Languages, and Applications | programming languages | `acm-sigplan-conference-on-object-oriented-programming-systems-languages-and-applications` |
| ICFP | ACM SIGPLAN International Conference on Functional Programming | functional programming | `acm-sigplan-international-conference-on-functional-programming` |
| CAV | International Conference on Computer Aided Verification | formal verification | `international-conference-on-computer-aided-verification` |
| LICS | ACM/IEEE Symposium on Logic in Computer Science | logic in CS | `acm-ieee-symposium-on-logic-in-computer-science` |
| SIGMOD | ACM SIGMOD International Conference on Management of Data | database flagship | `acm-sigmod-international-conference-on-management-of-data` |
| VLDB | International Conference on Very Large Data Bases | database flagship | `international-conference-on-very-large-data-bases` |
| ICDE | IEEE International Conference on Data Engineering | data engineering | `ieee-international-conference-on-data-engineering` |
| STOC | ACM Symposium on Theory of Computing | theory flagship | `acm-symposium-on-theory-of-computing` |
| FOCS | IEEE Symposium on Foundations of Computer Science | theory flagship | `ieee-symposium-on-foundations-of-computer-science` |

## 输出格式

```text
[目标会议 / Target] <venue> (<Acronym>)
[匹配度 / Fit] High / Medium / Low（一句话理由）
[贡献类型] algorithm / theory / system / dataset / benchmark / empirical / design / security / other
[最大证据缺口] <最关键的缺失证明/实验/研究/artifact/政策项>
[官方需复核项] CFP / author kit / DDL / 格式 / 匿名 / 伦理 / AI 使用 / artifact / rebuttal / camera-ready
[最高退稿风险] <该会场特有风险>
[改投建议] <若不匹配，给出更契合的会议或期刊>
[下一步] 打开 skills/<slug>/SKILL.md 做单会 fit 与当年周期核对
```

---
_内容来源：整合自 awesome-journal-skills 的 `Computer-Science-Conference-Skills` 元包（155 会议画像 + cs-ai-conference-workflow 路由 + resources，逐字保留于本 skill 的 `skills/` 与 `resources/`）。会议规则以官方当年 CFP 为准。_