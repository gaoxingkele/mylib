# PatentARA 调用指南

## 安装

```bash
# 进入项目目录
cd D:\aicoding\mylib\paa\engine\patent_ara

# 无外部依赖（纯 stdlib），可选依赖：
pip install pyyaml jsonschema  # YAML 支持和 schema 校验
```

## 快速开始

### 1. 解析专利文本

```python
from patent_ara import PatentParser

# 中文专利
parser = PatentParser(lang="zh")
ara = parser.parse("""
发明名称：一种数据处理方法

技术领域
本发明涉及数据处理技术领域。

权利要求书
1. 一种数据处理方法，其特征在于，包括以下步骤：
S1，获取数据；
S2，处理数据。
""")

print(f"标题: {ara.metadata.title}")
print(f"权利要求: {len(ara.claims)} 条")
for claim in ara.claims:
    print(f"  权{claim.number}: {len(claim.elements)} 个要素")
```

### 2. 权利要求分解

```python
from patent_ara import ClaimDecomposer

decomposer = ClaimDecomposer(lang="zh")
claims = decomposer.decompose_block("""
1. 一种方法，其特征在于，包括：
步骤A；
步骤B。
2. 根据权利要求1所述的方法，其特征在于，步骤A包括子步骤A1。
""")

for c in claims:
    print(f"权{c.number}: {c.claim_type}, {c.category}")
    for e in c.elements:
        print(f"  {e.id}: {e.element_type} - {e.text[:50]}")
```

### 3. Incopat 真实检索

```python
from patent_ara import IncopatIntegrator

integrator = IncopatIntegrator()  # 自动读取 credentials.json
ara = integrator.enrich_ara(ara, max_citations=5)

for cit in ara.citations:
    print(f"{cit.id}: {cit.patent_number} - {cit.title}")
    print(f"  绑定要素: {cit.mapped_element_ids}")
```

### 4. LLM 元素级评估

```python
from patent_ara import LLMEvaluator

llm_eval = LLMEvaluator()  # 自动读取 DEEPSEEK_API_KEY
verdicts = llm_eval.evaluate_against_citation(ara, "R1")

for v in verdicts:
    print(f"{v.element_id}: {v.status} ({v.confidence:.2f})")
```

### 5. CNIPA 三步法评估

```python
from patent_ara import Evaluator

evaluator = Evaluator(ara)
eval_report = evaluator.evaluate(verdicts)

print(f"Overall: {eval_report['overall']['score']:.3f}")
print(f"Grade: {eval_report['overall']['grade']}")

for cr in eval_report["claims"]:
    print(f"权{cr['number']}: novel={cr['novel']}, score={cr['claim_score']:.3f}")
    print(f"  区别特征: {len(cr['three_step']['step2_distinguishing_features'])}")
```

### 6. PAA 四门禁

```python
from patent_ara import GateKeeper

# 先注入客体适格判定
ara.subject_matter = {
    "eligible": True,
    "article": "25/2.2",
    "rationale": "属于技术手段"
}

gatekeeper = GateKeeper(ara, eval_report)
gate_report = gatekeeper.run_all()

print(f"Summary: {gate_report['summary']}")
for g in gate_report["gates"]:
    print(f"{g['gate']}: {'PASS' if g['passed'] else 'FAIL'}")
```

### 7. AHP-SEM 评分

```python
from patent_ara import integrate_scoring

scoring_report = integrate_scoring(ara, eval_report)
print(f"Score: {scoring_report['scores']['overall']:.3f}")
print(f"Recommendation: {scoring_report['recommendation']}")
```

### 8. 导出 PAA 目录

```python
from patent_ara import export_paa

paa_path = export_paa(ara, "output/my_patent", gate_report, scoring_report)
print(f"PAA exported to: {paa_path}")
```

## 完整工作流程

```python
from patent_ara import (PatentParser, IncopatIntegrator, LLMEvaluator,
                        Evaluator, GateKeeper, integrate_scoring, export_paa)

# 1. 解析
ara = PatentParser(lang="zh").parse(patent_text)
ara.subject_matter = {"eligible": True, "rationale": "技术手段"}

# 2. 检索
ara = IncopatIntegrator().enrich_ara(ara, max_citations=5)

# 3. LLM 评估
verdicts = LLMEvaluator().evaluate_all_citations(ara)

# 4. 三步法评估
eval_report = Evaluator(ara).evaluate(verdicts)

# 5. 四门禁
gate_report = GateKeeper(ara, eval_report).run_all()

# 6. 评分
scoring_report = integrate_scoring(ara, eval_report)

# 7. 导出
export_paa(ara, "output/my_patent", gate_report, scoring_report)

# 8. 保存/加载
ara.save("my_patent.patentara.json")
ara2 = PatentARA.load("my_patent.patentara.json")
```

## 命令行用法

```bash
# 运行测试
cd patent_ara
python tests\test_patent_ara.py

# 运行完整示例
python examples\full_pipeline_example.py

# 运行集成测试（含 Incopat + LLM）
python examples\integrated_full_test.py
```

## 配置

### Incopat 凭证

编辑 `D:/aicoding/mylib/paa/skills/incopat-search/scripts/credentials.json`，或设置同名 `INCOPAT_*` 环境变量。运行时环境变量优先：

```json
{
  "base": "https://apitest.incopat.com",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "username": "your_username",
  "password": "your_password"
}
```

### DeepSeek API Key

设置环境变量：

```bash
set DEEPSEEK_API_KEY=sk-your-key
set DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

或直接在代码中传入：

```python
from patent_ara import DeepSeekClient, LLMEvaluator

client = DeepSeekClient(api_key="sk-your-key")
llm_eval = LLMEvaluator(llm_client=client)
```

## 输出格式

### PatentARA JSON

```json
{
  "schema_version": "1.1.0",
  "metadata": {...},
  "cognitive": {
    "claims": [...],
    "claim_elements": [...]
  },
  "artifacts": {...},
  "exploration_graph": {...},
  "trace": {...},
  "subject_matter": {...}
}
```

### 评估报告

```json
{
  "overall": {
    "score": 0.805,
    "grade": "strong",
    "novel_claims": [1, 2, 3],
    "anticipated_claims": []
  },
  "claims": [...]
}
```

### 门禁报告

```json
{
  "passed": false,
  "summary": "FAIL (2 blocking)",
  "gates": [...]
}
```

## 注意事项

1. **禁编造专利号**：所有对比文件必须来自真实检索（Incopat）
2. **来源标记**：所有 AI 生成内容自动标记 `provenance="ai-executed"`
3. **门禁一票否决**：Gate1/2/4 失败会阻塞流程
4. **元素级评估**：LLM 评估是可选的，可用模拟数据替代
