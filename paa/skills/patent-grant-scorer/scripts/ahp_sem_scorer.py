# -*- coding: utf-8 -*-
"""专利授权成功率 AHP+SEM 多专家评分器

输入: 案件评分 JSON（4 位专家对 16 项可观测指标打 1-9 分）
输出: AHP 权重聚合 + SEM 结构方程映射 → 授权成功率预测

体系结构（三层 AHP + SEM 潜变量）:
  目标层  授权成功率 P(grant)
  准则层  5 个潜变量(SEM ξ):
    S 客体适格性(专利法2.2/25条, 门槛变量)
    N 新颖性(22.2)
    I 创造性(22.3, 权重最大)
    D 充分公开与支持(26.3/26.4)
    Q 撰写质量与保护范围
  指标层  16 项可观测指标(SEM 测量模型), 见 INDICATORS

多专家: 审查员/代理人/无效请求人/数据分析师 4 视角,
AHP 组决策用几何平均聚合, 一致性比率 CR<0.1 校验。
SEM 结构路径: logit(P) = β0 + βN·N + βI·I + βD·D + βQ·Q, 再乘客体门槛因子 g(S)。
路径系数以领域授权基线(incoPat 实测)校准。
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ---------- 测量模型: 潜变量 -> 指标(载荷) ----------
INDICATORS = {
    "S": {  # 客体适格性
        "S1": ("技术问题-技术手段-技术效果链完整度", 0.45),
        "S2": ("技术特征占比(vs 纯商业规则/智力活动)", 0.35),
        "S3": ("算法与具体应用场景/内部结构结合度", 0.20),
    },
    "N": {  # 新颖性
        "N1": ("最接近现有技术语义相似度反向分(1-简单换算)", 0.40),
        "N2": ("X文件不存在置信度(查新实证)", 0.35),
        "N3": ("独权特征组合在检索中的未命中度", 0.25),
    },
    "I": {  # 创造性
        "I1": ("区别特征的非显而易见性(非常规手段)", 0.35),
        "I2": ("特征间协同效应(1+1>2, 非简单叠加)", 0.30),
        "I3": ("Y文件组合启示不存在度", 0.20),
        "I4": ("有益效果的可信增益(定量/可验证)", 0.15),
    },
    "D": {  # 充分公开
        "D1": ("关键参数/公式/阈值具体化程度", 0.40),
        "D2": ("实施例完整度(可复现性)", 0.35),
        "D3": ("效果数据可验证性(无夸大禁词)", 0.25),
    },
    "Q": {  # 撰写质量
        "Q1": ("独权保护范围与支撑的平衡", 0.40),
        "Q2": ("从权梯度退守布局充分性", 0.35),
        "Q3": ("术语一致性与清楚性", 0.25),
    },
}

# ---------- AHP 准则层: 4 专家两两比较矩阵(对 N,I,D,Q; S 为门槛不参与加权) ----------
# 顺序 [N, I, D, Q]; a[i][j] = 准则 i 相对 j 的重要性(Saaty 1-9)
EXPERT_MATRICES = {
    "examiner":  # 严格审查员: 创造性主导, 公开其次
        [[1, 1/3, 1, 2], [3, 1, 3, 4], [1, 1/3, 1, 2], [1/2, 1/4, 1/2, 1]],
    "attorney":  # 资深代理人: 撰写质量能救创造性, 权重相对均衡
        [[1, 1/2, 1, 1], [2, 1, 2, 2], [1, 1/2, 1, 1], [1, 1/2, 1, 1]],
    "invalidator":  # 无效请求人: 盯新颖性与公开缺陷
        [[1, 1, 2, 3], [1, 1, 2, 3], [1/2, 1/2, 1, 2], [1/3, 1/3, 1/2, 1]],
    "analyst":  # 数据分析师: 按驳回理由统计分布(创造性>客体>公开>新颖性)
        [[1, 1/4, 1/2, 1], [4, 1, 3, 4], [2, 1/3, 1, 2], [1, 1/4, 1/2, 1]],
}

RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12}


def ahp_weights(matrix):
    """特征向量法(几何平均近似) + CR 一致性检验"""
    n = len(matrix)
    gm = [1.0] * n
    for i in range(n):
        p = 1.0
        for j in range(n):
            p *= matrix[i][j]
        gm[i] = p ** (1.0 / n)
    s = sum(gm)
    w = [g / s for g in gm]
    # λmax
    lam = 0.0
    for i in range(n):
        row = sum(matrix[i][j] * w[j] for j in range(n))
        lam += row / w[i]
    lam /= n
    ci = (lam - n) / (n - 1)
    cr = ci / RI[n] if RI[n] else 0.0
    return w, cr


def group_weights():
    """几何平均聚合 4 专家判断矩阵 → 组权重"""
    names = list(EXPERT_MATRICES)
    n = 4
    agg = [[1.0] * n for _ in range(n)]
    per_expert = {}
    for name in names:
        w, cr = ahp_weights(EXPERT_MATRICES[name])
        per_expert[name] = {"weights": w, "CR": round(cr, 4)}
        assert cr < 0.1, f"{name} 判断矩阵 CR={cr:.3f} >= 0.1, 需修正"
    for i in range(n):
        for j in range(n):
            p = 1.0
            for name in names:
                p *= EXPERT_MATRICES[name][i][j]
            agg[i][j] = p ** (1.0 / len(names))
    gw, gcr = ahp_weights(agg)
    return gw, gcr, per_expert


# ---------- SEM 结构模型 ----------
# 领域基线(incoPat 2019-2024 实测, 软件方法类 B 占比 20%-30%):
# 校准: 潜变量组合分 x∈[1,9] 映射 logit; x=5(中等)→P≈基线0.42(近年未决案折算),
# x=7→P≈0.72, x=3→P≈0.15   =>  logit(P)=k·(x-x0), k=0.65, x0=5.6
import math


def sem_probability(latent, weights):
    """latent: {'S':..,'N':..,'I':..,'D':..,'Q':..} 1-9 分"""
    N, I, D, Q = latent["N"], latent["I"], latent["D"], latent["Q"]
    wN, wI, wD, wQ = weights
    x = wN * N + wI * I + wD * D + wQ * Q
    p_core = 1.0 / (1.0 + math.exp(-0.65 * (x - 5.6)))
    # 客体门槛因子: S>=6 不惩罚; S<6 指数惩罚; S<=3 视为高危(封顶 0.15)
    S = latent["S"]
    if S >= 6:
        g = 1.0
    elif S > 3:
        g = 0.55 + 0.15 * (S - 3)
    else:
        g = min(0.15 / max(p_core, 1e-6), 0.35)
    p = p_core * g
    return round(p, 3), round(x, 2), round(p_core, 3)


def latent_scores(case_scores):
    """测量模型: 专家平均指标分 → 潜变量分。case_scores[expert][indicator]=1..9"""
    experts = list(case_scores)
    latent = {}
    detail = {}
    for lv, inds in INDICATORS.items():
        val = 0.0
        ind_avg = {}
        for code, (_name, loading) in inds.items():
            avg = sum(case_scores[e][code] for e in experts) / len(experts)
            ind_avg[code] = round(avg, 2)
            val += loading * avg
        latent[lv] = round(val, 2)
        detail[lv] = ind_avg
    return latent, detail


def grade(p):
    if p >= 0.70: return "A(高把握,建议直接申报)"
    if p >= 0.55: return "B+(较高,小修后申报)"
    if p >= 0.40: return "B(中等,需实质性强化)"
    if p >= 0.25: return "C(偏低,建议重构独权)"
    return "D(高危,建议合并/放弃或转其他保护)"


def score_case(case):
    gw, gcr, per_expert = group_weights()
    latent, ind_detail = latent_scores(case["scores"])
    p, x, p_core = sem_probability(latent, gw)
    return {
        "case": case["case"], "title": case.get("title", ""),
        "grant_probability": p, "grade": grade(p),
        "composite_x": x, "p_before_subject_gate": p_core,
        "latent": latent, "indicators": ind_detail,
        "group_weights": {"N": round(gw[0], 3), "I": round(gw[1], 3),
                          "D": round(gw[2], 3), "Q": round(gw[3], 3)},
        "group_CR": round(gcr, 4),
        "expert_CR": {k: v["CR"] for k, v in per_expert.items()},
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 自检: 输出权重体系
        gw, gcr, per = group_weights()
        print(json.dumps({"group_weights_NIDQ": [round(w, 3) for w in gw],
                          "group_CR": round(gcr, 4),
                          "per_expert": per}, ensure_ascii=False, indent=2))
        sys.exit(0)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    cases = data if isinstance(data, list) else [data]
    out = [score_case(c) for c in cases]
    print(json.dumps(out, ensure_ascii=False, indent=2))
