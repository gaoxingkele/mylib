# Agent Hub SQLite 备份与换库

从 `tools/agent-hub` 运行以下命令。示例中的 `SOURCE` 是当前业务库的绝对路径，`BACKUP_DIR` 和 `ROTATION_DIR` 是新的专用目录。先创建父目录。业务库、归档及恢复文件放在支持 SQLite 锁与硬链接的本地磁盘，由业务服务账号控制访问；这些文件含项目正文与额度状态，应按项目权限管理。

## 日常备份与恢复演练

```text
python -m agent_hub.backup backup SOURCE BACKUP_DIR
python -m agent_hub.backup verify BACKUP_DIR
python -m agent_hub.backup restore BACKUP_DIR NEW_TEST_DB --revocations-from CURRENT_AUTHORIZED_DB
```

备份命令在线生成一致快照 `snapshot.sqlite3`，执行完整性和外键校验，将 SHA-256、文件大小、模式版本、表行数、确认序号写入 `snapshot.json`。完成后复制整个目录到独立存储，在目标位置执行 `verify`，再用新路径测试恢复，抽查已确认事件、wiki 正文和额度查询记录。恢复到已有路径会失败。校验清单与快照应来自授权备份存储；SHA-256 用于核对副本一致性。

恢复含 wiki 正文的旧快照时必须提供拥有最新撤回状态的可信业务库。恢复器会重放这些撤回并清除派生正文，然后才发布恢复副本。实际切换时暂停权限与 wiki 可见性变更，核对撤权记录的备份时间和授权来源，在新服务开放查询前完成重放和验收。失去最新撤回依据时，保持旧备份离线并找回授权记录。历史归档和已有离线副本始终通过单独的备份权限、加密和保留期管理。

日备和轮换使用同一套格式。试点可先保留最近 7 份日备和 180 天归档，并按容量与项目留存要求调整。删除前核对待裁决证据、合法留存及独立可恢复副本。单台服务器损失时可恢复到最近备份及可补传记录所覆盖的时间；跨机试点前登记允许的数据损失窗口、备份频率和恢复时长。

## 切换新一代热库

1. 每 30 天或热库整理后约 256 MiB 时评估轮换。WAL 明显增大时先检查长读事务和 checkpoint，业务正文持续增长时核对 wiki 的有效版本与未处理任务。备份和热库占用分别计量。
2. 暂停**此业务 MCP** 的接入与采集器领取，等待正在处理的事务结束。本机 Hook 持久队列继续保存结果。终端中继、终端进程和现有 mylib 读取服务独立运行。
3. 执行 `python -m agent_hub.backup rotate SOURCE ROTATION_DIR`。工具检查磁盘余量、给原业务库加持久写入围栏，然后备份、校验、构建新库。若换库期间出错，保留原路径及轮换目录，按下节回退。预检失败且原库仍开放时，可直接恢复原服务。
4. 命令成功后，结果中的 `active` 指向 `ROTATION_DIR/active.sqlite3`。将业务服务的数据库启动参数切到该路径后启动服务，再继续用量采集。配置/进程管理器负责这一次路径切换。写入围栏会拒绝仍持旧路径的业务写入。
5. 检查服务健康、最新任务及额度池，补交一条已有事件并核对原回执，再提交一个新步骤。把 `ROTATION_DIR/archive` 复制到独立介质并执行 `verify`。同步通知路径变更给后续备份任务。

新热库带入近 7 天明细，保留 35 天内回执、全部待处理及带有效租约的额度任务、最新额度及上次成功值、现有 wiki 头版本和仍被引用的分支。单执行且已完结超过 30 天、全部额度任务已结案的任务可转冷。多执行的接力和交叉验证任务保守保留，私有归档内保存完整历史和原清单。全局序号跨轮换递增。如有效 wiki 当前版本、未决任务或用户的保留策略已经超过容量目标，应单独调整归档策略或存储预算。

## 异常与回退

```text
python -m agent_hub.backup rollback SOURCE ROTATION_DIR
```

- 原库封存后、下一代尚未写入时，此操作会核对专属轮换标识和新库逻辑摘要，封存新库并重新开放原库。随后将业务服务指回原路径，恢复受理。
- 若下一代已接受步骤、写入用量或更新租约，命令返回 `new_generation_changed_reconciliation_required`。继续保留两代完整数据。优先让兼容的旧版程序读取新一代数据库；若必须换回原代，应在停写期间导出、核对并迁移新增确认事件、wiki 版次、额度任务和快照，再切换。该跨代合并当前需要单独演练。
- 如果轮换中断，查看轮换目录中的 `rotation.json`，原库存在相同的写入围栏时可原地执行 `rollback`。维护目录与数据库写权限留给运维身份。
- `restore` 会生成新的运行副本，适合灾难恢复和演练。切换恢复副本前核对确认序号及后续补传来源，避免同时启用两个可写代次。

本机验收使用临时数据库，覆盖在线快照、恢复副本、坏校验拒绝、磁盘不足、轮换中途失败、旧库写入围栏、去重与序号延续、wiki 分支、待查额度与最新成功快照、换库前后回退条件。运行 `python -m unittest discover -s tests -p test_backup.py -v` 可重现。

## 已有 wiki 写入器的同步与撤回

在受控的 wiki 写入器生成 Markdown 后，使用同一执行的配置文件登记已批准的正文。配置中 `wiki_share_dir` 是项目内被授权共享的一个相对目录，可指向 `.metarsi/wiki`。外部写入器生成的文件按原字节读取并核对 SHA-256，来源文件保留。示例中的 `CONFIG` 对应已有项目、执行及机器认证关系；连接凭据通过授权环境提供。

```text
python -m agent_hub.wiki_sync --config CONFIG share-file --path omx_wiki/result.md --entry decision-a --version v1 --sha256 APPROVED_SHA256
python -m agent_hub.wiki_sync --config CONFIG flush
python -m agent_hub.wiki_sync --config CONFIG share-file --path omx_wiki/result.md --entry decision-a --version v2 --parent v1 --sha256 REVISED_SHA256
python -m agent_hub.wiki_sync --config CONFIG flush
python -m agent_hub.wiki_sync --config CONFIG withdraw --entry decision-a
python -m agent_hub.wiki_sync --config CONFIG flush
```

共享文件先进入本机持久队列；原项目须已有该来源上报的任务执行。修订使用 `wiki:write`，权限限定到项目。文件带有私有标记或已知凭据时需要先生成可分享的版本。每个文档版次可回查固定内容；相同父版的两个修订分别保留。纯文档修订独立于额度查询。

撤回由有 `wiki:withdraw` 授权的主体提交。登记撤回会清理此本机队列中相同项目及记录的待发正文。收到中央撤回回执后，项目内该记录各版及引用它的任务摘要从可查询数据中移除，失效版本的延迟提交会被拒绝。若需重新共享，经授权提炼新记录并使用新条目标识。既有的项目本地 wiki 文件可由原项目继续按本机授权保存。可运行 `python -m unittest discover -s tests -p test_wiki_sync.py -v` 验证。
