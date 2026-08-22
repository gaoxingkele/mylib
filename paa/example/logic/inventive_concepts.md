# 创造性点（认知层）

### C01: 知识图谱三层增强分工（查询 / 检索 / 生成）

- **Statement**: 图谱的角色不是单一"第三检索源"，而是分别承担查询理解、检索校验、生成约束三种角色，三者协同形成闭环。
- **Status**: CONFIRMED
- **Proof**:
  - → application/specification.md §embodiment_1（步骤 1-8 端到端实现）
  - → logic/prior_art.md §D01（CN121636664A 无三层分工）/ §D02（CN121659916A 止步生成端）
  - → evidence/scoring/scoring.json → I1=5.5, I2=6.0
- **非显而易见性**：对比文件 1 把图谱当加法召回源，对比文件 2 把图谱当约束事实源；两者均未把图谱定位为"三层分工"——需同时改造两份文件的架构才能得到本案方案，无结合启示。

### C02: 检索层路径惩罚"减法"校验（与现有"加法"扩召回相反）

- **Statement**: 对违背图谱关联路径的候选施加惩罚因子降权——这是图谱的"减法"用法，与现有"加法"扩召回相反方向。
- **Status**: CONFIRMED
- **Proof**:
  - → application/specification.md §embodiment_1 step 4
  - → logic/prior_art.md §D01（CN121636664A 仅做加法，无减法校验）
  - → evidence/scoring/scoring.json → I2=6.0
- **非显而易见性**：加法扩召回应是检索端的常规思路（多数对比文件走这条路）；减法降权需判断"什么不该出现在结果里"，技术思路相反。

### C03: Seal-and-Adapt 生成约束（封箱裁决 + 元适配门控，零注入）

- **Statement**: 不向提示词注入任何约束事实/指令；约束通过①封箱可用性裁决（隔离态根本不进模型输入）+ ②元策略对象门控（结构化控制配置而非文本）实现。
- **Status**: CONFIRMED
- **Proof**:
  - → application/specification.md §embodiment_1 step 6-8
  - → logic/prior_art.md §D02（CN121659916A "把结构化事实注入约束性提示模板"——本案用结构隔离替换该机制）
  - → evidence/scoring/scoring.json → I3=6.0
- **非显而易见性**：注入式约束是当前主流做法；本案要求"把注入这个动词整个替换掉"，需要同时放弃文本注入（区别于"换内容不换机制"的常规迭代），无提示技术意义。

### C04: 三引擎动态权重 RRF（按查询类型分类）

- **Statement**: RRF 融合的通道权重 w_r 不是固定的来源权重，而是按查询类型（实体/语义/精确）动态确定。
- **Status**: CONFIRMED
- **Proof**:
  - → application/specification.md §embodiment_1 step 2-3
  - → logic/prior_art.md §D01（CN121636664A 固定来源权重，无动态路由）
  - → evidence/scoring/scoring.json → I1=5.5