#!/usr/bin/env python3
"""
集成测试：Incopat + LLM + Scorer + PAA Export 全流程。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from patent_ara import (Citation, ElementVerdict, Evaluator, GateKeeper,
                        IncopatIntegrator, LLMEvaluator, PatentParser,
                        export_paa, integrate_scoring)

# ========== 1. 解析专利文本 ==========
CN_FULL = """
发明名称：一种基于深度学习的设备故障诊断方法及系统

技术领域
本发明涉及设备故障诊断技术领域，具体涉及一种基于深度学习的设备故障诊断方法及系统。

背景技术
现有技术中，设备故障诊断主要依赖人工经验，准确率低、效率低。已有一些基于机器学习的方法，但泛化能力不足。

发明内容
本发明提供一种基于深度学习的设备故障诊断方法，解决现有技术准确率低、泛化能力不足的问题。

附图说明
图1是本发明实施例的故障诊断方法流程图。
图2是本发明实施例的神经网络结构示意图。

具体实施方式
如图1所示，获取设备运行数据，包括振动信号、温度信号、电流信号。对运行数据进行预处理，包括归一化和降噪。将预处理后的数据输入训练好的深度学习模型，得到故障诊断结果。深度学习模型采用卷积神经网络结构，包括卷积层、池化层、全连接层。处理器(101)执行上述步骤，存储器(102)存储模型参数。

权利要求书
1. 一种基于深度学习的设备故障诊断方法，其特征在于，包括以下步骤：
S1，获取设备运行数据，所述运行数据包括振动信号、温度信号、电流信号；
S2，对所述运行数据进行预处理，包括归一化和降噪；
S3，将预处理后的数据输入训练好的深度学习模型，得到故障诊断结果；
S4，所述深度学习模型采用卷积神经网络结构，包括卷积层、池化层、全连接层。
2. 根据权利要求1所述的方法，其特征在于，所述预处理还包括特征提取。
3. 一种基于深度学习的设备故障诊断系统，其特征在于，包括：
数据获取模块，用于获取设备运行数据；
预处理模块，用于对所述运行数据进行预处理；
诊断模块，用于将预处理后的数据输入深度学习模型得到故障诊断结果。
"""

print("=" * 60)
print("Step 1: 解析专利文本")
print("=" * 60)
ara = PatentParser(lang="zh").parse(CN_FULL)
ara.subject_matter = {"eligible": True, "article": "25/2.2", "rationale": "技术手段"}
print(f"标题: {ara.metadata.title}")
print(f"权利要求: {len(ara.claims)} 条")

# ========== 2. 真实 Incopat 检索 ==========
print("\n" + "=" * 60)
print("Step 2: Incopat 真实检索")
print("=" * 60)
try:
    integrator = IncopatIntegrator()
    ara = integrator.enrich_ara(ara, max_citations=3)
    print(f"检索到 {len(ara.citations)} 篇对比文件")
    for c in ara.citations:
        print(f"  {c.id}: {c.patent_number} ({c.relevance}) - {c.title[:50]}")
except Exception as e:
    print(f"Incopat 检索失败: {e}")
    print("使用模拟数据继续...")
    # 添加模拟对比文件以便继续测试
    ara.citations.append(Citation(
        id="R1", patent_number="CN110123456A", title="基于神经网络的故障诊断",
        kind="retrieved", relevance="X", relationship="conflicts",
        mapped_element_ids=["C1.E1", "C1.E2"],
        search_receipt="mock search", claim_text_excerpt="一种基于神经网络的设备故障诊断方法...",
        verified=True
    ))

# ========== 3. LLM 元素级评估 ==========
print("\n" + "=" * 60)
print("Step 3: LLM 元素级评估")
print("=" * 60)
try:
    llm_eval = LLMEvaluator()
    # 只对第一篇对比文件评估（节省时间）
    if ara.citations:
        verdicts = llm_eval.evaluate_against_citation(ara, ara.citations[0].id)
        print(f"生成 {len(verdicts)} 条 LLM verdicts")
        for v in verdicts[:3]:
            print(f"  {v.element_id}: {v.status} ({v.confidence:.2f})")
    else:
        verdicts = []
        print("无对比文件，跳过 LLM 评估")
except Exception as e:
    print(f"LLM 评估失败: {e}")
    print("使用模拟 verdicts 继续...")
    # 模拟 verdicts
    verdicts = []
    for c in ara.claims:
        for e in c.elements:
            verdicts.append(ElementVerdict(
                element_id=e.id, reference_id="R1",
                status="disclosed" if e.id != "C1.E4" else "not_disclosed",
                confidence=0.9, rationale="模拟评估"
            ))

# ========== 4. 评估器 ==========
print("\n" + "=" * 60)
print("Step 4: CNIPA 三步法评估")
print("=" * 60)
evaluator = Evaluator(ara)
eval_report = evaluator.evaluate(verdicts)
print(f"Overall score: {eval_report['overall']['score']:.3f}")
print(f"Grade: {eval_report['overall']['grade']}")

# ========== 5. 四门禁 ==========
print("\n" + "=" * 60)
print("Step 5: PAA 四门禁")
print("=" * 60)
gatekeeper = GateKeeper(ara, eval_report)
gate_report = gatekeeper.run_all()
print(f"Summary: {gate_report['summary']}")
for g in gate_report["gates"]:
    status = "PASS" if g["passed"] else "FAIL"
    print(f"  {g['gate']}: {status}")

# ========== 6. 评分 ==========
print("\n" + "=" * 60)
print("Step 6: AHP-SEM 评分")
print("=" * 60)
scoring_report = integrate_scoring(ara, eval_report)
print(f"Overall: {scoring_report['scores']['overall']:.3f}")
print(f"Recommendation: {scoring_report['recommendation']}")

# ========== 7. 导出 PAA ==========
print("\n" + "=" * 60)
print("Step 7: 导出 PAA 目录")
print("=" * 60)
output_dir = Path(__file__).parent / "paa_output"
paa_path = export_paa(ara, output_dir, gate_report, scoring_report)
print(f"PAA 导出到: {paa_path}")
print("生成的文件:")
for f in sorted(paa_path.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(paa_path)}")

print("\n" + "=" * 60)
print("集成测试完成！")
print("=" * 60)
