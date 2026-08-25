#!/usr/bin/env python3
"""
完整示例：PatentARA + PAA 门禁 + 评估 全流程。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from patent_ara import (ClaimVersion, Citation, DeadEnd, DesignAround,
                        ElementVerdict, Evaluator, GateKeeper, PatentParser)

# ========== 1. 解析专利文本为 PatentARA ==========
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
print(f"标题: {ara.metadata.title}")
print(f"权利要求数: {len(ara.claims)}")
for c in ara.claims:
    print(f"  权{c.number}: {c.claim_type} {c.category}, {len(c.elements)} 个要素")

# ========== 2. 注入客体适格判定 (Gate 1) ==========
print("\n" + "=" * 60)
print("Step 2: 客体适格判定")
print("=" * 60)
ara.subject_matter = {
    "eligible": True,
    "article": "25/2.2",
    "rationale": "属于技术手段，涉及信号处理与深度学习模型",
    "analyzed_by": "agent"
}
print(f"适格: {ara.subject_matter['eligible']}")
print(f"理由: {ara.subject_matter['rationale']}")

# ========== 3. 添加对比文件 (真实检索结果) ==========
print("\n" + "=" * 60)
print("Step 3: 添加对比文件")
print("=" * 60)
# 模拟从 incopat-search 获取的真实对比文件
ara.citations.append(Citation(
    id="R1",
    patent_number="CN110123456A",
    title="基于神经网络的设备故障诊断方法",
    kind="retrieved",
    relevance="X",
    relationship="conflicts",
    mapped_element_ids=["C1.E1", "C1.E2", "C1.E3"],
    search_receipt="incopat semantic search: 深度学习+故障诊断",
    claim_text_excerpt="一种基于神经网络的设备故障诊断方法，包括获取设备运行数据...",
    verified=True
))
ara.citations.append(Citation(
    id="R2",
    patent_number="CN110654321B",
    title="设备状态监测系统",
    kind="retrieved",
    relevance="A",
    relationship="background",
    mapped_element_ids=["C3.E1"],
    search_receipt="incopat expression: TI-CN=(故障诊断)",
    verified=True
))
print(f"对比文件: {len(ara.citations)} 篇")
for c in ara.citations:
    print(f"  {c.id}: {c.patent_number} ({c.relationship}, verified={c.verified})")

# ========== 4. 模拟 LLM 元素级评估 ==========
print("\n" + "=" * 60)
print("Step 4: 元素级评估 (模拟 LLM verdicts)")
print("=" * 60)
verdicts = []
for c in ara.claims:
    for e in c.elements:
        # R1 披露了 C1 的大部分要素，除了 E4 (CNN结构细节)
        if e.id == "C1.E4":
            status = "not_disclosed"
            excerpt = ""
        elif e.claim_number == 1:
            status = "disclosed"
            excerpt = "对应权1相关段落"
        else:
            status = "not_disclosed"
            excerpt = ""
        verdicts.append(ElementVerdict(
            element_id=e.id,
            reference_id="R1",
            status=status,
            confidence=0.9,
            rationale=f"基于文本比对{'披露' if status == 'disclosed' else '未披露'}",
            evidence_excerpt=excerpt
        ))

print(f"生成 {len(verdicts)} 条元素级 verdicts")

# ========== 5. 运行评估器 ==========
print("\n" + "=" * 60)
print("Step 5: 运行评估器 (CNIPA 三步法)")
print("=" * 60)
evaluator = Evaluator(ara)
eval_report = evaluator.evaluate(verdicts)
print(f"Overall score: {eval_report['overall']['score']:.3f}")
print(f"Grade: {eval_report['overall']['grade']}")
for cr in eval_report["claims"]:
    print(f"  权{cr['number']}: novel={cr['novel']}, score={cr['claim_score']:.3f}")
    if cr["three_step"]["step2_distinguishing_features"]:
        print(f"    区别特征: {len(cr['three_step']['step2_distinguishing_features'])} 条")

# ========== 6. 运行四门禁 ==========
print("\n" + "=" * 60)
print("Step 6: 运行 PAA 四门禁")
print("=" * 60)
gatekeeper = GateKeeper(ara, eval_report)
gate_report = gatekeeper.run_all()

print(f"总体: {gate_report['summary']}")
for g in gate_report["gates"]:
    status = "PASS" if g["passed"] else "FAIL"
    print(f"  {g['gate']}: {status}")
    if g["findings"]:
        for f in g["findings"][:2]:
            print(f"    - {f}")

# ========== 7. 添加探索图轨迹 ==========
print("\n" + "=" * 60)
print("Step 7: 添加探索图轨迹")
print("=" * 60)
ara.claim_versions.append(ClaimVersion(
    id="CV1", claim_number=1, version=1,
    text=ara.claims[0].text,
    change_rationale="初始版本",
    provenance="user"
))
ara.claim_versions.append(ClaimVersion(
    id="CV2", claim_number=1, version=2,
    text="修改后的权1文本...",
    change_rationale="区别特征强化：明确 CNN 结构细节",
    supersedes="CV1",
    provenance="ai-executed"
))
ara.design_arounds.append(DesignAround(
    id="DA1",
    target_feature="C1.E4",
    mechanism_substitution="从通用深度学习模型改为具体 CNN 结构",
    prior_art_id="R1",
    provenance="ai-suggested"
))
ara.dead_ends.append(DeadEnd(
    id="DE1",
    direction="纯算法权利要求",
    reason="客体适格风险（智力活动规则）",
    provenance="ai-executed"
))
print(f"权利要求版本: {len(ara.claim_versions)}")
print(f"设计绕行: {len(ara.design_arounds)}")
print(f"被否方向: {len(ara.dead_ends)}")

# ========== 8. 保存与加载 ==========
print("\n" + "=" * 60)
print("Step 8: 序列化保存")
print("=" * 60)
output_path = Path(__file__).parent / "example_output.patentara.json"
ara.save(output_path)
print(f"已保存: {output_path}")

# 验证可以重新加载
ara_loaded = type(ara).load(output_path)
print(f"重新加载成功: {len(ara_loaded.claims)} 条权利要求, {len(ara_loaded.citations)} 篇对比文件")

print("\n" + "=" * 60)
print("全流程完成！")
print("=" * 60)
