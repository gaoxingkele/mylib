# 评审依据记录格式

`scripts/validate_review_basis.py` 本地读取JSON，返回 `errors` 和 `warnings`。无网络、模型调用或新增依赖。它检查来源适用性声明与引用关系，不读取引用正文，不能证明法规、标准、采用条款、授权或项目事实真实。格式允许额外字段，便于与修订台账共用；原台账的 `status` 等规则仍由 `validate_revision_ledger.py` 检查。

## 项目记录

顶层必须有 `context`、非空 `sources` 和非空 `records`。

| 区域 | 字段 | 含义 |
|---|---|---|
| context | funder、call_id、project_type | 当前申报方、具体批次和项目类别标识；同轮使用一致值 |
| context | stage | application、midterm、acceptance、follow_up |
| context | as_of | YYYY-MM-DD，固定本轮判断日期 |
| source | id、title | 唯一编号与实际题名 |
| source | kind | call、template、enterprise_rule、standard、regulation、method、guide_case、historical_case、standard_plan |
| source | status | current、historical、superseded、draft、unknown；根据实际核验填写 |
| source | read_level | full_text、excerpt、metadata；全文、节选或仅题录，不为过检查夸大读取范围 |
| source | funder、call_id | 适用机构与批次；`general`为跨机构来源。call/template作为硬要求时须与本轮call_id明确相同；通用制度可用enterprise_rule并按真实范围声明 |
| source | stages、project_types | 非空字符串数组；明确通用时可填all，不能把未知范围写成all |
| source | url / source_path | 至少提供一个实际来源位置 |
| source | effective_date | 可选生效日期，YYYY-MM-DD；不以发布日期推定生效日 |
| source | standard_type | standard来源可选mandatory、recommended、guidance，默认recommended；推荐/指导代码（GB/T、GB/Z、DL/T、NB/T等）不能标成mandatory |
| record | id、project_id、location、quote、basis、suggestion | 唯一意见号、项目、原文定位、短引、依据和可执行建议 |
| record | claim_type | requirement、recommendation、inference、catalog_fact |
| record | source_ids、source_loci | 引用编号数组及`编号: 原文位置`映射；catalog_fact可不提供loci，其他类型必须逐来源提供 |
| record | applicability | applicable、conditional、not_applicable、unknown；未核定不能作为明确违规依据 |
| record | adoptions | 可选逐来源采用声明数组，见下文 |

`requirement`表示意见按当前要求检查缺陷。来源需已读正文或相应节选、当前有效、已生效且范围匹配。计划、历史案例和方法资料不能自行成为硬要求；标准推荐/指导属性也不自动变成强制属性。明确适用的强制性标准另核原文和范围。

`recommendation`或`inference`用于学习参考与可选增强，允许不同体系、历史资料和题录入口，但输出警告提醒其未验证为本轮硬性依据。`catalog_fact`仅记录题名、编号、状态等题录事实，不得冒充标准条文或项目违规结论。

### 明确采用的来源

本轮文件采用某推荐标准或跨范围来源时，记录：

```json
{"source_id":"STD01","adopted_by":"CALL01","locus":"附件技术要求第3条","explanation":"本轮该条明确指定STD01用于此任务的测试。"}
```

两个编号必须存在；采用者是本轮适用、有效且已读原文的call/template/enterprise_rule，不能自引用。按来源分别记录，不能用一份无关本轮文件替所有参考标准作背书。未生效、非现行、计划或题录来源不能凭采用声明绕过检查；此类冲突应先核定。即使检查通过，采用声明仍有“内容真实性未验证”的警告。

## 可运行的合成示例

以下是格式演示，不是真实申报制度。`synthetic-call.md`代表本地合成材料，内容假定为“申报方案须说明测试集和验证责任”。题录参考仍是题录，不能据此宣称电力大模型标准规定了某一达标百分比。

```json
{
  "context": {"funder":"synthetic_grid","call_id":"example-2026","stage":"application","project_type":"software","as_of":"2026-10-10"},
  "sources": [
    {"id":"CALL01","title":"合成申报要求","kind":"call","status":"current","read_level":"full_text","funder":"synthetic_grid","call_id":"example-2026","stages":["application"],"project_types":["software"],"source_path":"synthetic-call.md"},
    {"id":"STD01","title":"人工智能 电力行业大模型评测指标和方法","kind":"standard","standard_type":"guidance","status":"current","read_level":"metadata","funder":"general","stages":["all"],"project_types":["all"],"url":"https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=9AE5C9990CD2337EF7093499C3F0E20F"}
  ],
  "records": [
    {"id":"RV01","project_id":"EXAMPLE","location":"方案第2段","quote":"拟开展系统评测。","basis":"CALL01第1条要求说明测试集和验证责任。","suggestion":"写明测试集形成方法和验证负责人。","claim_type":"requirement","source_ids":["CALL01"],"source_loci":{"CALL01":"第1条"},"applicability":"applicable"},
    {"id":"RV02","project_id":"EXAMPLE","location":"方案第2段","quote":"拟开展系统评测。","basis":"STD01题录可作为后续精读的电力评测参考入口。","suggestion":"取得全文并核定适用条款后完善测试方案。","claim_type":"recommendation","source_ids":["STD01"],"source_loci":{"STD01":"官方题录：题名、编号与状态"},"applicability":"conditional"}
  ]
}
```

保存为 `example-basis.json` 后运行：

```powershell
python proposal-writing/scripts/validate_review_basis.py example-basis.json -o example-basis-check.json
```

退出码：0为声明/结构检查通过，可能仍有软参考警告；1为校验不通过；2为文件读取/解析等执行错误。结果不包含原句全文。错误信息指向意见号和来源编号。

## 领域能力profile

`--profile`检查用于共享的公开领域参考包。私有项目来源使用前面的basis记录，不能混入公开profile。字段为：

- `schema_version: "1.0"`、`domain: "power_grid"`、`verified_at: YYYY-MM-DD`。
- `sources`使用上述来源结构并必须有http(s)公开URL，不含source_path或明显本地URL；合法的历史、未知状态和metadata资料可以用于学习，不据此作为硬要求。URL声明不证明来源实际公开可访问，仍需人核验。
- `competencies`各含id、name、`type: "inference"`、owner_roles（1—6整数数组）、source_ids、review_questions、failure_pattern、evidence_to_request和transfer_limit。

检查唯一编号、引用存在、合法角色与非空内容，不限定卡片或问题数量。它不检查文字判断是否专业，也不证明推断得到了标准全文支持。已声明仅题录的能力参考仍应由审查者按需精读。
