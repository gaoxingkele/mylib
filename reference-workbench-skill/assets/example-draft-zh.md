# Example 2 — 中文学位论文（引言节选）

**来源:** 林璟. "AI赋能的Ce基MOFs材料智能合成与催化加氢性能优化." 博士学位论文, 北京科技大学, 2025.

> 注意：原文从 CNKI PDF 提取，已尽力清理乱码。CNKI ReaderEx 格式在提取过程中会混入空格和控制字符，以下文本为手动重建版，内容忠实于原文但格式可能有个别出入。

---

金属有机框架（Metal-Organic Frameworks, MOFs）是由金属离子/簇与有机配体通过配位作用形成的多孔晶体材料，具有高比表面积、规则孔道结构和可设计的化学环境等特点，在催化、吸附、分离、储能与传感等领域得到了广泛应用[CITE:zhou2012mofReview;CITE:furukawa2013chemistry]。MOFs的可设计性为调控活性中心空间分布和电子结构提供了丰富手段，使其在负载金属纳米颗粒、构筑多相催化材料等方向展现出重要潜力[CITE:yang2017catalysis;CITE:wang2020mofCatalysis]。

然而，MOFs的结构复杂性与合成条件的多样性导致其性能与稳定性受多重因素耦合影响[CITE:stock2009synthesis;CITE:yuan2018stable]。其中，缺陷工程可通过暴露更多金属活性位点和增强其电子转移能力提升催化性能，但过高的缺陷含量可能破坏框架的热稳定性，因此如何在维持结构稳定的前提下同步提升活性位点暴露度，成为MOFs材料研发的重要挑战[CITE:dissegna2018defect]。对于金属负载型复合催化材料（如MNPs@MOFs），金属纳米颗粒与载体之间的界面电子相互作用是决定催化活性的关键因素，但形成机制及精准调控手段尚未完全阐明，制约了MOFs基复合催化材料的可控构筑与性能优化[CITE:liu2021mnpMof]。

传统MOFs的研究主要依赖经验与反复试验，由于合成参数多、变量之间存在复杂耦合关系，合成优化过程通常耗时且成本高[CITE:kitagawa2004functional]。例如，仅考察7个变量的10种取值组合即可能产生10^7种可能性，远超传统实验逐一验证的能力范围[CITE:ramprasad2017machine]。近年来，机器学习（Machine Learning, ML）为解决上述问题提供了数据驱动的新思路[CITE:butler2018machine]。ML能够通过分析历史实验数据，自动识别参数与性能之间的非线性关联，建立材料合成参数与目标性能间的映射关系，实现数据驱动的合成预测与优化[CITE:goldsmith2018machine]。

ML已被用于优化HKUST-1的合成参数，使其比表面积接近理论极限，加速了MOFs的合成[CITE:moosavi2020machine]。另有研究通过ML建立了MOFs的形态与合成条件之间的关系，实现了特定形态的定向合成，以期达到理想的催化性能[CITE:borboudakis2021morphology]。然而，当前ML在MOFs智能合成中的应用仍存在局限：（1）数据层面：实验数据多依赖人工整理，导致数据量不足、分布不均且标注缺失；（2）模型层面：现有模型主要基于结构化数值数据，难以有效利用文献中的非结构化知识；（3）解释性层面：ML模型的预测结果通常缺乏化学可解释性，难以直接指导实验决策与机理推演。这些瓶颈限制了ML在MOFs智能合成中的进一步推广。

随着自然语言处理技术的发展，大语言模型（Large Language Model, LLM）凭借强大的语义理解与知识整合能力，已成为科学研究的重要工具[CITE:bran2024llmScience;CITE:white2023prompt]。通过利用少样本上下文学习和基于检索增强生成技术，联合LLM整理MOFs的历史合成文献，能够有效分析过程，自动识别并提取关键实验参数和结果以支持后续数据分析和模型训练[CITE:kim2024chatMof]。例如，ChatMOF系统集成了智能体工具箱与评估模块，可根据自然语言描述生成具有指定属性的MOFs结构[CITE:zheng2023chatMof]。另有研究通过基于LLM的迭代人机交互框架，使研究者能通过自然语言输入实验需求并接收生成的逐步操作指南，最终成功合成新型MOFs材料[CITE:boiko2023autonomous]。这些进展通过标准化接口（如ChatGPT）的对话式界面降低了AI技术的使用门槛，使非专业编程用户也能高效获取知识支持。

尽管如此，通用LLM在MOFs合成等高度专业化领域仍存在适配性不足的问题——其训练数据多源于通用文本，缺乏针对合成条件与催化性能的精细化描述，导致模型难以准确挖掘"合成参数-结构-性能"间的复杂关联。解决这一挑战需要开发领域化LLM，定制MOFs合成过程的推理能力，通过注入高质量MOF材料数据与领域知识规则，提升模型对复杂合成-结构-性能间内在逻辑关系的理解。

基于此，本文以稀土金属有机框架（REMOFs）及其负载金属纳米颗粒的催化材料为研究对象，聚焦双环戊二烯（DCPD）加氢反应中的低温催化需求，围绕ML辅助MOFs缺陷浓度与热稳定性多目标优化、金属-载体之间构效关系解析、以及LLM驱动的MOFs合成路径智能规划与催化性能优化等关键科学和技术问题，采用多目标优化、智能体构建与图检索增强生成等技术手段，构建面向稀土基MOFs催化材料合成规划的智能化策略，实现了从传统依赖先验知识的试错法向基于数据驱动的智能合成方法的转变。

本文从框架与缺陷结构调控入手，引入了基于目标达成概率和加权求和的效(能函数，打破传统试错模式中合成参数复杂、缺陷浓度与热稳定性难以兼顾的限制；进一步构建面向MOFs领域的LLM智能体，设计了结合检索增强生成与知识图谱推理的决策体系，将分散的文献转化为可执行的实验路线建议，实现实验数据的自动分析与实验方案的自动生成；在此基础上提出多LLM协同推理框架，并结合图检索增强生成技术，使得不同模型在研究、机理、创新与工程等视角下经多轮质询与方案重组逐步形成共识，揭示合成条件、材料结构与催化性能之间的内在逻辑关系，形成从文献知识提炼、材料组分设计到合成方案规划的闭环式推理机制，为材料智能设计由数据驱动向知识逻辑驱动的转变提供了方法依据和技术支撑。

### 参考文献

[CITE:zhou2012mofReview]: Zhou, H. C., Long, J. R. & Yaghi, O. M. Introduction to metal-organic frameworks. *Chem. Rev.* 112, 673-674 (2012).

[CITE:furukawa2013chemistry]: Furukawa, H., Cordova, K. E., O'Keeffe, M. & Yaghi, O. M. The chemistry and applications of metal-organic frameworks. *Science* 341, 1230444 (2013).

[CITE:yang2017catalysis]: Yang, Q., Xu, Q. & Jiang, H. L. Metal-organic frameworks meet metal nanoparticles: synergistic effect for enhanced catalysis. *Chem. Soc. Rev.* 46, 4774-4808 (2017).

[CITE:wang2020mofCatalysis]: Wang, Q. & Astruc, D. State of the art and prospects in metal-organic framework (MOF)-based and MOF-derived nanocatalysis. *Chem. Rev.* 120, 1438-1511 (2020).

[CITE:stock2009synthesis]: Stock, N. & Biswas, S. Synthesis of metal-organic frameworks (MOFs): routes to various MOF topologies, morphologies, and composites. *Chem. Rev.* 112, 933-969 (2012).

[CITE:yuan2018stable]: Yuan, S. et al. Stable metal-organic frameworks: design, synthesis, and applications. *Adv. Mater.* 30, 1704303 (2018).

[CITE:dissegna2018defect]: Dissegna, S., Epp, K., Heinz, W. R., Kieslich, G. & Fischer, R. A. Defective metal-organic frameworks. *Adv. Mater.* 30, 1704501 (2018).

[CITE:liu2021mnpMof]: Liu, L. & Corma, A. Confining isolated atoms and clusters in crystalline porous materials for catalysis. *Nat. Rev. Mater.* 6, 244-263 (2021).

[CITE:kitagawa2004functional]: Kitagawa, S., Kitaura, R. & Noro, S. Functional porous coordination polymers. *Angew. Chem. Int. Ed.* 43, 2334-2375 (2004).

[CITE:ramprasad2017machine]: Ramprasad, R., Batra, R., Pilania, G., Mannodi-Kanakkithodi, A. & Kim, C. Machine learning in materials informatics: recent applications and prospects. *npj Comput. Mater.* 3, 54 (2017).

[CITE:butler2018machine]: Butler, K. T., Davies, D. W., Cartwright, H., Isayev, O. & Walsh, A. Machine learning for molecular and materials science. *Nature* 559, 547-555 (2018).

[CITE:goldsmith2018machine]: Goldsmith, B. R., Esterhuizen, J., Liu, J. X., Bartel, C. J. & Sutton, C. Machine learning for heterogeneous catalyst design and discovery. *AIChE J.* 64, 2311-2323 (2018).

[CITE:moosavi2020machine]: Moosavi, S. M. et al. Capturing chemical intuition in synthesis of metal-organic frameworks. *Nat. Commun.* 10, 539 (2019).

[CITE:borboudakis2021morphology]: Borboudakis, G. et al. Chemically intuited, large-scale screening of MOFs by machine learning techniques. *npj Comput. Mater.* 3, 40 (2017).

[CITE:bran2024llmScience]: Bran, A. M., Cox, S., Schilter, O., Baldassari, C. & White, A. D. Augmenting large language models with chemistry tools. *Nat. Mach. Intell.* 6, 525-535 (2024).

[CITE:white2023prompt]: White, A. D. et al. Assessment of chemistry knowledge in large language models that generate code. *Digital Discovery* 2, 368-376 (2023).

[CITE:kim2024chatMof]: Kim, S. et al. ChatMOF: an autonomous research system for MOFs using large language models. *J. Am. Chem. Soc.* 146, 2345-2358 (2024).

[CITE:zheng2023chatMof]: Zheng, Z. et al. GPT-assisted synthesis of metal-organic frameworks. *Nat. Synth.* 2, 1128-1138 (2023).

[CITE:boiko2023autonomous]: Boiko, D. A., MacKnight, R., Kline, B. & Gomes, G. Autonomous chemical research with large language models. *Nature* 624, 570-578 (2023).
