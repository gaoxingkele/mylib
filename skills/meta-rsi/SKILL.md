---
name: meta-rsi
description: metaRSI 证据账本与准入控制。做实验、筛规则、改受保护文件之前先查账和过门；实验结束后记录证据等级、被否决的想法和预登记的影子规则。适用于任何由代理推进的研究项目。
---

# metaRSI

代理在一个项目里反复「提想法 → 做实验 → 改规则」时，用它管三件事：这条证据算哪一级、哪些数据和文件不能动、哪些想法已经试过。它不调用任何模型，也不替人做决定。

本技能目录（mylib）只放代码、默认配置（`config/defaults.json`）和说明。用它的项目把全部状态放在自己的 `.metarsi/` 下：

| 文件 | 作用 |
|---|---|
| `constitution.json` | 受保护面、证据等级、项目不变量。`init` 生成一次，之后只由人修改 |
| `metarsi.db` | SQLite。`events` 表只追加、逐条哈希相连，是唯一的记录；`windows / trials / negatives / shadows / admissions / episodes` 是每次写入后由它重建的查询表 |
| `wiki/` | LLM wiki 风格的 Markdown：`README.md`（入口和当前状态）、`graph.md`（证据图）、`nodes.md`、`trials.md`、`negatives.md`、`ideas.md`（想法与思考算子）、`log.md`、`playbooks.md`。每次写入后由数据库重写，供人、代理和 git diff 阅读，不要手改 |

查已有结论时，代理可以直接读 `wiki/` 下的页面，或对 `metarsi.db` 写 SQL；写入只走命令。

```
python C:/aicoding/mylib/skills/meta-rsi/scripts/metarsi.py --project <项目根目录> <命令>
```

## 学习还是进化：`tick`

每个用户回合开始实质工作之前调用一次 `tick`（本地运行，不联网，不调用模型）。它根据账本和项目日历给出当前模式：

| 模式 | 什么时候 | 代理怎么做 |
|---|---|---|
| 后台学习 | 默认。没有到期的影子规则，也没有「既有理由、又有办法验证」的改进 | 照常干活和记录；描述性分析可以做，但只算 in_sample 或 reused_holdout；不在已用过的窗口上搜新规则当验证 |
| 进化（验证阶段） | 有影子规则到了成熟天数 | 只为这条规则读一次保留窗口并计分，然后记录、结案，通过再提议 |
| 进化（留出验证） | 有待处理的信号，且有未用过的留出窗口 | 在开发数据上选定规则，由代码在留出窗口上计分一次；避开已疲劳的类别 |
| 进化（只能登记影子） | 有待处理的信号，但没有未用过的留出窗口 | 提出假设并登记成影子规则，等保留窗口成熟 |

进化要同时有两样：一个理由（影子到期、用户提出改进要求、故障或漂移累积到阈值），和一条比「再看一遍用过的数据」更强的验证途径。缺一样就是后台学习。判断只用实测的东西：窗口状态、成熟天数、信号条数、最近试验的结论、弱证据到强证据的保持率；不用模型自报的置信度。

信号从哪来：

- 用户提出改进或新实验的要求：`signal log --kind request --name ...`
- 项目运行出故障、指标漂移：`signal log --kind failure|drift`，或在项目脚本里调用 `emit_signal(项目根目录, kind, name, note)`
- 处理完：`signal resolve --id G0001 --note ...`

模式变化会记入账本，当前模式和理由写在 `wiki/README.md` 顶部。用户明确要求的分析不受模式限制，照做并说明它能达到的证据等级；模式只约束代理自己发起的改进。阈值在 mylib 的 `config/defaults.json` 的 `policy` 里，项目可以在 `constitution.json` 里用同名字段覆盖；成熟天数靠 `constitution.json` 的 `calendar`（文件名即日期的目录加持有期长度）计算。

### 让宿主自动调用：Claude Code 钩子

`hook` 子命令是给宿主钩子用的入口：从标准输入读钩子的 JSON，算出当前模式，用 `additionalContext` 注入上下文。会话开始时注入完整说明，之后每次用户发消息只注入一两行；模式变了才再给完整说明，并提示代理告诉用户。它不会拦住用户的消息：出错时只显示一条警告。目录里没有 `.metarsi/constitution.json` 的项目，它什么都不输出。

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "timeout": 20,
      "command": "python \"C:/aicoding/mylib/skills/meta-rsi/scripts/metarsi.py\" hook"}]}],
    "UserPromptSubmit": [{"hooks": [{"type": "command", "timeout": 20,
      "command": "python \"C:/aicoding/mylib/skills/meta-rsi/scripts/metarsi.py\" hook"}]}]
  }
}
```

放在项目的 `.claude/settings.json` 里只对该项目生效；放在 `~/.claude/settings.json` 里对所有项目生效（没用 metaRSI 的项目不受影响）。项目目录取环境变量 `CLAUDE_PROJECT_DIR`，没有就取钩子输入里的 `cwd`。装了钩子之后，Claude Code 里不必再手动 `tick`；Codex 等没有钩子的宿主仍靠 `AGENTS.md` 的约定。

## 其余四个时点

除了每回合的 `tick`，在下面四个时点调用：

1. **开始一个实验之前**
   - `idea suggest [--problem 一句话]`：想法从哪来。工具按本项目账本挑出几条没用过的思考算子（跨至少两个层次），给出问句和陷阱；代理按问句想，再 `idea add` 登记。见下节「创意演化」。
   - `search <关键词>`：这个想法是否已经试过、为什么被否决。
   - `check --read 起..止 --write 路径`：要读的日期是否碰到保留窗口，要写的文件是否受保护。返回码 2 表示违规，停下来告诉用户，不要绕过。
2. **实验出结果之后**
   - `trial log`：每条有结论的规则记一条。等级由工具按「规则在哪段数据上选定、在哪段数据上计分」算出，不能自报。附上结果文件（`--artifact`）。
   - 否决的想法另记 `negative add`，写清原因和教训；对应的想法 `idea update --status rejected --link N0001`。进了试验的 `--status trialed --link T0001`；采纳必须带试验或准入编号。
3. **提出「以后再验」的规则时**
   - `shadow add`：把规则原文、指标、窗口、最少成熟天数写死。一个窗口只能有一条 `--primary`；换主用 `shadow primary --id --by <用户名>`，旧主规则留痕退为并列。
4. **想改受保护的文件时**
   - `propose --surface 路径 --evidence 试验编号`：证据等级不够直接拒绝；够了也只会变成 `pending_human`。
   - `decide` 只在用户明确指示后执行，并写上用户的名字（`--by`）。代理不能批准自己的提议。

每个用户回合结束时可以用 `episode log` 记一条问答摘要，和项目的 wiki 会话记录对应。

## 创意演化：想法从哪来、怎么算数

改进不能只靠「把已有要素再组合一下」。工具不产生想法，但管三件事：想法的**来源**（用了哪个思考算子）、想法的**可检验性**（什么观测能推翻它）、各类算子在本项目里的**产出**。算子目录在 `config/ideation.json`，分五个层次，详解见 [references/IDEATION.md](references/IDEATION.md)：

| 层次 | 内容 | 例子 |
|---|---|---|
| L1 组合与调参 | 并置已有机制、调阈值 | 常规改进；审查里最容易被认定为显而易见 |
| L2 科学第一性原理 | 守恒与收支、极限与量纲、物理/信息上界、时间尺度分离、对称与破缺、不变量与比值、因果反转、限速步、可观测性 | 「不可测的那一项能否安排一个时段让它退出方程」→ 新的标定窗口 |
| L3 哲学视角 | 现象学（被给予之物）、可证伪性、奥卡姆与减法、范畴检查、先验条件、矛盾与前提改变、过程哲学、知道与假定、约束作资源 | 「受体真正接收的是什么量」→ 控制目标换成受体侧量 |
| L4 社会学视角 | 实践与惯习、问责与信任、可见性与规训、行动者网络、采用与扩散、可及性、规范作输入、外部性、社会建构的判据 | 「出了事谁负责」→ 责任边界做成许可位和不可绕过的联锁 |
| L5 跨域类比 | 结构同构、生物类比、历史先例 | 方程形式相同的另一领域的解法 |

用法：

1. 提改进前 `idea suggest [--problem 一句话] [--n 3]`。工具按账本挑最少用过的层次和算子（L1 不在推荐之列），至少跨两个层次，打印问句、会得到什么、陷阱。代理按问句去想；问句不是答案。
2. 每条想法 `idea add --title ... --operator L2.conservation --premise <所用的原理或视角> --claim <想法> --falsifier <能推翻它的观测>`。没有证伪条件的想法工具不收——这是把波普尔那条算子做成了硬规则。
3. 想法的状态只有五个：seed → screened → trialed → adopted | rejected。`adopted` 必须 `--link` 一个试验或准入编号；凭意见不能算采纳。想法本身始终是 `judge` 级，证据等级只属于它关联的试验。
4. `idea stats` 看按层次和按算子的产出；`tick`/钩子在最近 N 条想法里组合类超过一半时提醒换视角。这就是工具的「学习」：不是模型学，而是账本累积出「在这个项目里哪类思考方式真的出过成果」，并把代理从组合惯性里推出来。
5. 项目可以在 `constitution.json` 的 `ideation.extra_operators` 里加自己的算子（同样的 id/level/name/question 字段），`ideation.policy` 覆盖 `recent_n`、`max_combination_share`、`suggest_n`。

不做的事：工具不给想法打分、不排序、不用模型生成候选；哪个想法值得试仍由代理和人判断，判断的依据写进 `--premise` 和 `--falsifier`。

## 模型审计：训练和外推

规则类的结论靠证据等级管；模型另有一类毛病是证据等级看不出来的：评估时用的模型和上线的模型不是同一个，或者模型学到的东西换一段行情就不成立。`model` 命令把这类问题变成可以登记、可以按固定规则检查的事实。工具不读模型文件，事实由项目脚本量出来再登记。

```
model register --name N --role shipped|candidate|reference --recipe "做法的文字描述" \
               [--trees 2,39,37,40] [--market-gain 0.7]
model block --name N --block 2025Q2 --relation oos|fit|tune --metric-name 每笔 --value 0.69 \
            [--days 61] [--fit-days 250] [--scored-by 别的模型名] [--profile ma20_up=0.98 --profile ma20_up_market=0.38]
model audit [--name N]        按规则列出每个模型的问题
model diagnose               把各模型的样本外区块摆在一起：一起失效（问题在行情）还是各自失效（互补）
propose ... --model N         提议里带上模型，审计有问题就直接拒绝
```

| 检查 | 要登记的事实 | 判为有问题 |
|---|---|---|
| 评估和上线是同一个模型 | 每个区块的分数是谁打的（`--scored-by`） | 有区块的分数来自别的模型 |
| 同一做法产出同一类模型 | 各次训练的树数（`--trees`） | 最少的不到 5 棵，或最多最少相差 5 倍以上 |
| 拟合窗口够长 | 每次拟合用了多少个交易日（`--fit-days`） | 最短的不到 120 天 |
| 样本外区块够多、过半为正 | 区块和训练数据的关系（`--relation`）与指标值 | 自己打分的样本外区块不到 3 个，或为正的不到一半 |
| 外推没有损失大半 | 拟合 / 调参窗口内与样本外的指标 | 窗口内为正，样本外不到它的一半 |
| 样本外没有前好后差 | 按时间排的样本外区块 | 至少 4 个区块时，较早的一半平均为正、最近的一半平均不为正 |
| 学的是股票而不是日子 | 全市场同值特征的增益占比（`--market-gain`） | 超过 50% |
| 选股没有极端偏向 | 选股画像：名单的某个比例和全市场的同一比例（`--profile k=…`、`k_market=…`） | 两者相差超过 0.3 |

阈值在 `config/defaults.json` 的 `policy.model` 里，项目可以在 `constitution.json` 里覆盖。上线模型有审计问题时，`tick` 会提示它的历史成绩要打折。

`model diagnose` 回答的是下一步往哪用力。做法不同的模型在同一批区块一起失效，说明原因在模型之外，继续改训练做法没有用，该去管仓位和风控；模型在不同区块失效，说明它们互补，该验证的是组合或按行情切换。它只是把已登记的数字分类，结论仍要到保留窗口上验。

训练一个要长期用的模型，按这个顺序做（也写在 `wiki/playbooks.md`）：

1. 把做法写死：窗口怎么取、树多少棵、特征怎么处理。每一折和最终模型都用它，不让早停在不同窗口上产出不同的东西。
2. 被评估的每个区块都排在训练数据之后；拟合窗口、调参窗口、样本外分开报。
3. 把上线模型放回历史上它没见过的日子重新打分；引用成绩只用它自己打的分。
4. 量树数、全市场同值特征的增益占比、选股画像，登记后跑 `model audit`。
5. 审计干净、并且在保留窗口上按影子规则验过，才提议进合约。

## 证据等级

从强到弱：

| 等级 | 含义 |
|---|---|
| `formal` | 机器检查：测试、类型检查、逐行复现 |
| `prospective` | 规则先登记成影子，再在登记时没读过的数据上计分 |
| `holdout_once` | 规则在别的数据上选定，在留出数据上第一次为这类问题计分 |
| `reused_holdout` | 留出数据已经为同一类问题用过 |
| `in_sample` | 规则就是在这段数据上看出来的 |
| `judge` | 模型或人的判断，没有结果数据支撑 |

`judge` 级的意见（包括 JEV、LLM 评审、代理自评）可以用来排查遗漏，不能当作改动受保护文件的证据。同一类问题在同一个窗口上比较过的规则数会累计，`trial log` 和 `status` 会给出按 Bonferroni 折算后需要的 |t|。

## 常用命令

```
init --name <项目名>                       建 .metarsi/（宪法、数据库、wiki），constitution.json 之后由人编辑
tick                                      判断后台学习还是进化，并列出现在可以做和不做的事
hook                                      宿主钩子入口：读标准输入的钩子 JSON，输出要注入上下文的 JSON
signal log --kind request|failure|drift|opportunity --name ... [--note ...]
signal resolve --id G0001 --note ...
status                                    窗口、影子、待批提议、账本是否完整
window add --name N --start D [--end D] --state open|consumed|reserved
trial log --rule-id R --family F --selected-on W1 --scored-on W2 [--shadow S] \
          --n-compared K --effect X --t T --verdict pass|fail|inconclusive --artifact 文件
negative add --idea ... --reason ... --lesson ... [--trial T0001]
idea suggest [--problem ...] [--n 3]         按账本挑没用过的思考算子（跨层次），给问句和陷阱
idea add --title ... --operator L2.conservation --premise ... --claim ... --falsifier ...
idea update --id I0001 --status screened|trialed|adopted|rejected [--link T0001|N0001|P0001] [--note ...]
idea stats | idea list                     各层次/算子的产出；组合类占比超过一半会在 tick 里提醒
shadow add --rule ... --metric ... --window W --min-matured 60 [--primary]
shadow primary --id S0008 --by <用户名> --note ...   把窗口的主规则换到另一条未结影子（只有用户能换）
check --read 20260101..20260630 --write config/x.json [--shadow S0001 --matured 60]
propose --surface 路径 --summary ... --evidence T0003 [--check 复现=pass]
decide --id P0001 --approve|--reject --by <用户名> --reason ...
calibration                               弱等级上显著的结果到强等级还剩多少
search 关键词...
verify-ledger                             检查账本有没有被改过
```

实验脚本里可以直接用：

```python
sys.path.insert(0, "C:/aicoding/mylib/skills/meta-rsi/scripts")
from metarsi import guard_read, reserved_from, emit_signal
guard_read(project_root, "20260127", "20260805")   # 碰到保留窗口会抛 PermissionError
emit_signal(project_root, "failure", "daily list empty", note="...")   # 项目运行时上报信号
```

## 边界

- 工具只在被调用时起作用，不拦截代理的其他操作。它是约定加记录，不是沙箱。
- 直接改 `events` 表能被 `verify-ledger` 发现，但不能阻止；查询表和 wiki 页面改了也没用，下次写入会按 `events` 重建。真正的防线是 git 和人的审查。
- 不自动改合约、不自动交易、不自动提交。受保护面的最终决定永远是人。
- 不生成想法、不给想法打分。`idea suggest` 只是按账本轮换思考算子并复述问句；想法的好坏由随后的试验说话。
- 设计来源、与原始六层方案的对应关系、以及哪些部分没有实现，见 [references/DESIGN.md](references/DESIGN.md)。
