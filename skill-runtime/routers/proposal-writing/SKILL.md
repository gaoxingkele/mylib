---
name: proposal-writing
description: 申报书统一路由。用于国自然、国社科、省部级科研基金、科技项目、教改项目及人才计划的材料梳理、提纲、逐节起草、审查和修订，按申报类别加载对应 skill；指南模板优先、事实可追溯、缺项待补。论文和专利使用各自模块。
metadata:
  source-root: "D:/aicoding/mylib/proposal-writing"
---

# 申报书入口

维护源是 `D:/aicoding/mylib/proposal-writing`。

先读取 [主模块](../../../proposal-writing/SKILL.md)，再按其中分类表只加载本次所需的适配说明和上游 skill。已有草稿需要多角色评审、仲裁或升级修订时，再读取主模块中的评审与修订路由。以当年指南和模板为准，材料编号可追溯，缺项标【待补】，禁止编造。

此运行时目录只暴露一个 skill，不链接完整子技能树；上游执行器仅在模块内部按需读取，不单独注册。
