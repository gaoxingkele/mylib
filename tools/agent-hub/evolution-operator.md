# Agent Hub 离线策略评测与版本回执

账本以项目、工具、工具版本和能力标识隔离范围。waiting-v1 评测「无输出即阻塞」与「仅凭当前可信信号提示阻塞」这一对固定规则。paired-artifact-v1 接收任意获准的不可变 skill 或 harness 工件，对比独立验证的同任务结果。发布更新该范围的活动版本指针，实际运行工件由宿主加载并回报。本地操作入口不修改 Git 或项目文件。

## 本地操作

在 Agent Hub 目录下以服务所有者身份运行。数据库放在授权的数据目录，遵循服务的访问权限和备份策略。参数 JSON 按方法的参数名称填写。写入操作的审计操作者通过命令行传入。

    python -m agent_hub.evolution --db PATH --actor OPERATOR register_baseline baseline.json
    python -m agent_hub.evolution --db PATH --actor OPERATOR propose trial.json
    python -m agent_hub.evolution --db PATH --actor OPERATOR --approved-evidence DEV_REVIEW evaluate development.json
    python -m agent_hub.evolution --db PATH --actor OPERATOR --approved-evidence HOLDOUT_REVIEW evaluate heldout.json
    python -m agent_hub.evolution --db PATH --actor OPERATOR promote approval.json
    python -m agent_hub.evolution --db PATH list_status project.json

初始化和预登记使用模块导出的 WAITING_BASELINE_VERSION 与 WAITING_CANDIDATE_VERSION。各 JSON 文件的参数如下。

| 操作 | 参数 |
| --- | --- |
| register_baseline | scope、skill_id、version |
| propose | scope、skill_id、candidate_id、version、parent_version、development_id、heldout_id，可选 evidence_kind、evaluator、provenance。默认 authorized 和 waiting-v1 |
| evaluate | scope、skill_id、candidate_id、split（development 或 heldout）、dataset_id、cases |
| promote | scope、skill_id、candidate_id、evaluation_digest。人工核对评测后填写当前摘要 |
| rollback | scope、skill_id、expected_version |
| revoke_evidence | scope、evidence_id |
| get_status | scope、skill_id，可选 candidate_id 或成对的 attempt_id 和 generation |
| list_status | project_id，可选 limit（1–50） |

scope 含 project_id、tool、tool_version 三个字段。waiting-v1 的样本提供 evidence_id、group_id、label（blocked、waiting、limited、clear）、observable、quiet_ms、signal（三类信号或空）、signal_delay_ms（从观察起点计算，无信号为空）及 trusted_current。独立评审者确认样本来源、标签、互不相关的观察组、统一观察期限、工具版本和授权状态。每组只提交一项配对观测，保留集已打开的分组不能再次使用。证据不足时，为同一规则版本登记新试验 ID 和新的保留集。

--approved-evidence 文件包含 scope、candidate_id、dataset_id、reviewer、case_sha256。最后一项把每个样本 ID 映射为其规范化 JSON 的 SHA-256。规范化采用 UTF-8 编码和 Python json.dumps 的 sort_keys=True、separators=(",", ":")、ensure_ascii=False。清单由授权评审者单独保管和填写。程序核对批次和样本内容，真实性、授权及独立性由评审者负责。合成演练把候选标记为 fixture，全流程使用独立数据库和 --fixture-sandbox。正常数据库可以记录合成评测，合成证据无法获准发布。

评测检查候选作用是否触发以及单边配对检验、误报率改善、重大安全退化和 p95 提醒延迟。开发集及保留集门槛分别为两类各 10 和 60 个独立组，最低误报率改善为 5 个百分点。证据撤权后重算该范围内的评测。当前版本失去依据时回到基线，查询只返回剩余证据的汇总。合成结果只证明流程可执行。

### 任意 skill 或 harness 的离线比较

首次登记时把基线实际工件的内容 SHA-256 作为版本。提议时设 evaluator 为 paired-artifact-v1，并提供 provenance.parent、provenance.candidate 和 provenance.verifier_sha256。每份工件描述包含 kind、完整 Git revision、库内相对 path 和正文 sha256。parent_version 和 version 分别等于父子内容摘要。父代必须是当前批准的版本，已有父代评测时也必须匹配其工件修订和路径。编译器、测试和运行设置固定在验收器摘要及任务工件中，发布标签或分支名不作为不可变引用。

每个样本包含 evidence_id、group_id、task_sha256、parent_run、candidate_run。两次分别执行，使用同一任务工件和验收器。每次运行记录 run_id、revision、asset_sha256、task_sha256、verifier_sha256、result_sha256、passed、critical_failure、effectful_violation 和 duration_ms。评审者依原始验收日志核对运行附件、实际生效的工件、完整任务输入、隔离范围与边界，再用受信清单记录样本摘要。独立性无法确认的样本不能用于放行。服务只核对摘要并计算成对结果，不启动验收命令。模型和普通 Hook 无法提交评测或自行批准。

开发集和保留集分别至少有 10 和 60 个父代通过及同样数量父代失败的独立组。最低实用通过率改善是 5 个百分点，采用一次预登记的单边配对检验。任何原先通过变失败、新增严重失败、候选越过受控操作边界或 p95 延迟增加超过 5 秒都会否决。样本在开发集与保留集之间按观察组、任务和运行 ID 去重。不同项目或工具版本各自验证，不能仅凭跨工具可读性扩大适用范围。

批准后须在工件清单登记被评测的同路径、Git 修订与内容摘要，宿主从该清单读取。较新试验须以上一获准版本为父代，可对同一项能力连续发布。普通回退选最近仍有效的父版。上游评测证据被撤回时，其发布后继的采用权限也失效。测试中两个连续版本的合法加载仅在隔离测试回调中演练，没有实际发布 mylib 工件，也没有给真实候选发放评测通过凭证。

### 共享 Wiki 证据撤回

使用共享 Wiki 的样本须另外提供 wiki_dependency，填写 entry_id、version 和正文 sha256。账本从当前业务库核对同项目的指定版本。服务器启动时绑定业务库，本地操作命令为此添加 --wiki-database PATH，指向当前权威业务库。操作员评审清单中的样本摘要须一并覆盖 wiki_dependency。现有未登记依赖的样本，以及外部证据、手工证据，仍由操作员按实际授权变化执行 revoke_evidence。

读取状态、发布和宿主加载前，账本检查业务库中持久化的撤回记录。即使业务库完成撤回后服务立即停止，重启后的第一次访问也会完成对账。撤回会使相关试验展示 evidence_revoked，隐藏评测摘要及旧版采用状态。已发布试验退回父版，待确认的旧请求失效。其他独立试验可继续发布。业务库不可读或指定的源版本无法核实时，依赖该来源的请求及项目级汇总会失败，精确查询独立试验仍可返回。恢复业务库时走既有撤回重放流程。

## 宿主接入

运行开始时调用 pin_attempt 取得固定版本。宿主实际加载成功后才发送 record_loading 启动回执。已发布版本和固定版本均可以先于实际回执存在。

用户选择一个在途执行并确认升级后，服务用 confirm_loading 固定请求、执行、代次和版本。宿主派发前调用 authorize_loading 消费确认。同一个请求只有一次派发许可。宿主可用 pending_restart 回报计划，生效后再发 loaded。应用前重新核对允许发布的版本与授权，执行代次变化时重新确认。派发结果未知时查询原请求状态，依宿主持久去重协议处理。旧代次回执不能更新当前窗口。

服务在读取时检查项目授权，派发与回执时另核对操作者、宿主身份及当前执行代次。模型使用只读汇总。采用账本使用独立 SQLite 文件时，备份、恢复及检查也分别运行。恢复前核对该账本和任务库的执行代次。

### 固定工件与真实加载

服务局部启用后，工件清单放在受限的绝对路径。启动配置提供清单 SHA-256，允许源端只取该清单中的任务级 skill 或 harness。每个条目记录 project、task_id、tool、tool_version、skill_id、version、kind、revision、path、sha256 和 size。revision 是完整 Git 版本，path 是该版本内的相对路径。每个文本工件上限 64 KiB，skill 为 Markdown，harness 为允许的文本或结构化配置。代码启动脚本及二进制文件不进入这条加载通道。使用本地工件根目录时读取 root/revision/path，也可以在条目登记 catalog_skill_id 及可选 catalog_resource，走已有中央 MCP 的固定修订读取。读取后复核字节数、摘要及修订。

宿主凭据需有 evolution:source，且其主体、主机、主机安装 ID、工具和账号与当前执行匹配。操作人凭据需有 tasks:read 和 evolution:confirm，并通过 evolution_hosts 与账号范围授权。预览和提交确认只走已有的独立控制入口，预览仅显示元数据。确认所选版本及工件摘要后，只有对应宿主可领取一次派发许可。权限撤回、改用其他执行或原版本撤回时，服务拒绝后续领取或回执。

宿主接入可以调用 adoption.load_task_asset。回调由宿主为当前工具实现，参数是目标、工件元数据及已校验的原始字节。实际生效后回调以 result=loaded、effective_sha256=实际生效内容摘要作证。等待下次加载可回报 pending_restart。上报 loaded 之前必须核对宿主本身的执行代次及配置；准备、下载和保存工件仅代表已经读取。隔离测试回调用合成配置检查此链路，实际 CLI 的读入位置、时序与回执需要逐个运行环境验证。
