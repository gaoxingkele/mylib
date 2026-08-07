# Journal deep distill notes (2026-08)

Root: `D:\aicoding\powergrid_benchmark\papers\literature\target_journal_related\fulltext_by_journal`

## elsevier-journal-of-energy-storage

- Deep sample: **n=10** PDFs under `fulltext_by_journal/elsevier-journal-of-energy-storage/`.
- **Length:** pages mean/median **25.4/20.0** (range 10–53); words mean/median **9966/9030**.
- **Structure:** sections mean **23.7**; paragraphs mean **54.0**; words/paragraph mean/median **203.8/147.0**.
- **Artifacts:** formulas≈**22.1**; figures≈**10.4**; tables≈**4.0**; block-diagrams≈**1.4** (mentions). Block-diagram sections: other×7, method×5, introduction×2, 1 Introduction×2, 0.8 Capacity×1, 2.3 Example data×1.
- **Experiment load:** datasets mentioned≈**0.6**/paper; named algorithms≈**1.9**/paper; baseline signal **7/10**; ablation/sensitivity **0/10**; strength histogram: {'strong': 2, 'solid': 5, 'moderate': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **156** words / **6.7** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 3), ('gap/background', 2), ('missing', 2)]).
- **Conclusion craft:** mean **221** words; dominant pattern: `restate contribution` (top [('restate contribution', 2), ('limitations', 2), ('missing', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~1037 words / ~6.5 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~522 words / ~3.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~250 words / ~2.0 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~335 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** However, Energy Storage, Energy, Hence, Thermal, Morocco, There, Li-ion, Renewable, Review, Furthermore, Group.
- **Frequent named algorithms:** attention(5), transformer(3), Kalman(2), LSTM(2), Transformer(1), CNN(1), GA(1), PSO(1).
- **Frequent dataset/benchmark cues:** dataset(2), Dataset(1), data set(1), IEEE 93(1), IEEE 1997(1).
- **Common sentence openings:** `Battery health prediction under generalized conditions`; `Howey July Abstract Accurately predicting the`; `The complex nature of degradation renders`; `This study predicts the changes in`; `These changes can be integrated against`; `The approach naturally incorporates varying current`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## ieee-internet-of-things-journal

- Deep sample: **n=10** PDFs under `fulltext_by_journal/ieee-internet-of-things-journal/`.
- **Length:** pages mean/median **10.4/9.5** (range 8–21); words mean/median **7032/6342**.
- **Structure:** sections mean **8.9**; paragraphs mean **47.6**; words/paragraph mean/median **145.0/144.6**.
- **Artifacts:** formulas≈**7.2**; figures≈**8.5**; tables≈**0.0**; block-diagrams≈**0.7** (mentions). Block-diagram sections: other×5, I I NTRODUCTION×2, III COVID-19×1, 5 TREC-COVID ad×1, 3 An integrated IoT-enabled machine lear×1.
- **Experiment load:** datasets mentioned≈**4.1**/paper; named algorithms≈**3.3**/paper; baseline signal **9/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 2, 'strong': 2, 'very_strong': 6}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **0** words / **0.0** sentences; dominant pattern: `missing` (top patterns [('missing', 10)]).
- **Conclusion craft:** mean **0** words; dominant pattern: `missing` (top [('missing', 10)]).
- **Chapter size/role (corpus means):**
  - **method**: avg ~408 words / ~3.0 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~1133 words / ~7.8 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
- **Frequent terms:** COVID-19, IEEE INTERNET, THINGS JOURNAL, IEEE, Internet, University, NOVEMBER, IoMT, Things, Online, Available, However.
- **Frequent named algorithms:** attention(6), CNN(5), SVM(4), LSTM(3), ResNet(2), XGBoost(2), random forest(2), PSO(2).
- **Frequent dataset/benchmark cues:** data set(8), IEEE 2020(5), dataset(4), IEEE 2021(3), Kaggle(3), DATA SET(3), benchmark(3), data
set(2).
- **Common sentence openings:** `IEEE INTERNET OF THINGS JOURNAL VOL`; `These value-added sensors have revolutionized the`; `These embedded sensors could also be`; `Governments and regulators are turning to`; `The outbreak of COVID-19 in December`; `The use of embedded sensors could`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## ijacsa

- Deep sample: **n=10** PDFs under `fulltext_by_journal/ijacsa/`.
- **Length:** pages mean/median **7.6/7.5** (range 4–10); words mean/median **5665/5106**.
- **Structure:** sections mean **14.4**; paragraphs mean **27.8**; words/paragraph mean/median **279.0/249.4**.
- **Artifacts:** formulas≈**7.5**; figures≈**6.5**; tables≈**1.4**; block-diagrams≈**0.9** (mentions). Block-diagram sections: other×6, 2 Background×1, 3 Data×1, 4.1 Proprocessing and Segmentation×1, II R ELATED WORK×1, IV M ETHODS×1.
- **Experiment load:** datasets mentioned≈**3.1**/paper; named algorithms≈**1.9**/paper; baseline signal **5/10**; ablation/sensitivity **0/10**; strength histogram: {'moderate': 3, 'solid': 4, 'strong': 2, 'very_strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 7, 'mixed': 2, 'algorithm_innovation': 1}).
- **Abstract craft:** mean **176** words / **7.8** sentences; dominant pattern: `gap/background` (top patterns [('gap/background', 3), ('method claim', 2), ('method claim → quantitative result', 1)]).
- **Conclusion craft:** mean **103** words; dominant pattern: `missing` (top [('missing', 5), ('restate contribution', 2), ('short wrap-up', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~468 words / ~3.5 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~654 words / ~5.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~802 words / ~4.9 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~424 words / ~4.0 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~205 words / ~1.7 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** International Journal, Applications, IJACSA, Advanced Computer Science, Each, First, Gain, LSTM, Good, Average, Third, Fail.
- **Frequent named algorithms:** SVM(3), attention(2), LSTM(2), Random Forest(2), Adam(2), CNN(2), SGD(2), GA(1).
- **Frequent dataset/benchmark cues:** data set(7), dataset(6), data 
set(3), Dataset(3), Data Set(3), DATA SET(2), benchmark(2), UCI(1).
- **Common sentence openings:** `IJACSA International Journal of Advanced Computer`; `In this research the classification task`; `It is split into five class`; `Lecturer Dept of MCA VBS Purvanchal`; `One way to achieve highest level`; `The knowledge is hidden among the`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## keai-unconventional-resources

_No readable PDFs._

## mdpi-algorithms

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-algorithms/`.
- **Length:** pages mean/median **26.6/22.0** (range 4–51); words mean/median **9510/7756**.
- **Structure:** sections mean **17.2**; paragraphs mean **64.0**; words/paragraph mean/median **145.4/147.2**.
- **Artifacts:** formulas≈**42.4**; figures≈**5.6**; tables≈**2.9**; block-diagrams≈**0.2** (mentions). Block-diagram sections: method×1, 2.1 The Original Quantum Approximate Opt×1, experiment×1, 4 Discussion×1.
- **Experiment load:** datasets mentioned≈**2.0**/paper; named algorithms≈**2.5**/paper; baseline signal **9/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 1, 'moderate': 3, 'strong': 3, 'thin': 1, 'very_strong': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'mixed': 1}).
- **Abstract craft:** mean **148** words / **6.7** sentences; dominant pattern: `missing` (top patterns [('missing', 3), ('gap/background → method claim', 2), ('gap/background → method claim → quantitative result', 1)]).
- **Conclusion craft:** mean **147** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 3), ('missing', 3), ('restate contribution', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~853 words / ~6.2 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~663 words / ~5.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~632 words / ~4.7 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~558 words / ~4.1 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~216 words / ~1.8 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Algorithms, Author Manuscript Author Manuscript, Author, However, While, Page, February, Hamming, Here, Algorithm, Hence, August.
- **Frequent named algorithms:** attention(4), GA(3), SVM(3), CNN(2), SGD(1), ResNet(1), TRansformer(1), Transformer(1).
- **Frequent dataset/benchmark cues:** dataset(7), Dataset(4), benchmark(3), data set(2), Benchmark(2), IEEE 1998(1), IEEE 2020(1).
- **Common sentence openings:** `Author Manuscript Author Manuscript Author Manuscript`; `Author manuscript available in PMC August`; `Author manuscript available in PMC February`; `Learning over Knowledge-Base Embeddings for Recommendation`; `However structured knowledge bases exhibit unique`; `When the explicit knowl- edge about`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## mdpi-atmosphere

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-atmosphere/`.
- **Length:** pages mean/median **26.7/27.5** (range 19–32); words mean/median **9311/8746**.
- **Structure:** sections mean **13.8**; paragraphs mean **63.0**; words/paragraph mean/median **143.8/144.6**.
- **Artifacts:** formulas≈**12.4**; figures≈**9.1**; tables≈**2.9**; block-diagrams≈**0.3** (mentions). Block-diagram sections: other×1, 2.1 Pellet Fuels×1, abstract×1, Abstract×1, back×1, References×1.
- **Experiment load:** datasets mentioned≈**0.7**/paper; named algorithms≈**0.9**/paper; baseline signal **8/10**; ablation/sensitivity **0/10**; strength histogram: {'moderate': 3, 'solid': 6, 'strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'mixed': 1}).
- **Abstract craft:** mean **96** words / **4.3** sentences; dominant pattern: `missing` (top patterns [('missing', 5), ('descriptive', 2), ('gap/background', 2)]).
- **Conclusion craft:** mean **186** words; dominant pattern: `limitations` (top [('limitations', 4), ('missing', 3), ('short wrap-up', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~840 words / ~6.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~37 words / ~1.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~447 words / ~3.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~610 words / ~4.7 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~369 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Atmosphere, Basel, Author, Page, EPA Author Manuscript EPA, Author Manuscript EPA Author, Manuscript, October, Health, PubMed, July, March.
- **Frequent named algorithms:** GA(6), Adam(2), attention(1).
- **Frequent dataset/benchmark cues:** dataset(4), Dataset(1), UCI(1), data set(1).
- **Common sentence openings:** `EPA Author Manuscript EPA Author Manuscript`; `Environmental Protection Agency Research Triangle Park`; `Environmental Protection Agency Washington DC USA`; `Conflicts of Interest The authors declare`; `Author manuscript available in PMC October`; `Author Manuscript Author Manuscript Author Manuscript`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## mdpi-future-internet

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-future-internet/`.
- **Length:** pages mean/median **27.4/27.5** (range 15–45); words mean/median **11585/11276**.
- **Structure:** sections mean **25.3**; paragraphs mean **49.9**; words/paragraph mean/median **415.0/238.0**.
- **Artifacts:** formulas≈**9.1**; figures≈**9.1**; tables≈**2.4**; block-diagrams≈**0.5** (mentions). Block-diagram sections: other×4, back×1, References×1, 4 Architecture×1, 4.2 Separable Convolution with Residual ×1, 5.2 Decentralized application implementa×1.
- **Experiment load:** datasets mentioned≈**1.7**/paper; named algorithms≈**2.5**/paper; baseline signal **8/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 4, 'thin': 1, 'very_strong': 3, 'strong': 1, 'moderate': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **160** words / **7.0** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 5), ('method claim', 2), ('gap/background', 2)]).
- **Conclusion craft:** mean **272** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 4), ('restate contribution', 3), ('limitations → future work', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~700 words / ~5.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~262 words / ~2.2 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~291 words / ~2.1 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~420 words / ~3.0 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
- **Frequent terms:** Future Internet, However, Internet, Author, Moreover, Thus, Proceedings, Things, Cloud, June, Author Manuscript Author Manuscript, Page.
- **Frequent named algorithms:** attention(4), GA(2), CNN(2), Adam(2), ResNet(2), Attention(2), ga(1), Random
Forest(1).
- **Frequent dataset/benchmark cues:** dataset(5), benchmark(3), Dataset(2), Benchmark(2), ETTH(1), IEEE 802(1), IEEE 2012(1), IEEE 11073(1).
- **Common sentence openings:** `Author Manuscript Author Manuscript Author Manuscript`; `We present both frameworks from the`; `The aim is to discuss and`; `We compare selected properties of both`; `Based on this comparison we evaluate`; `ONGERUBRICEERD ONGERUBRICEERD Nederlandse Organisatie voor toegepast-natuurwetenschappelijk`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## mdpi-information

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-information/`.
- **Length:** pages mean/median **26.5/23.5** (range 4–68); words mean/median **11516/11366**.
- **Structure:** sections mean **22.1**; paragraphs mean **58.4**; words/paragraph mean/median **225.6/149.4**.
- **Artifacts:** formulas≈**28.0**; figures≈**11.3**; tables≈**3.6**; block-diagrams≈**2.6** (mentions). Block-diagram sections: other×9, introduction×1, 1 Introduction×1, 6.1 Text and Document Feature Extraction×1, conclusion×1, 8 Conclusions×1.
- **Experiment load:** datasets mentioned≈**2.9**/paper; named algorithms≈**5.6**/paper; baseline signal **6/10**; ablation/sensitivity **1/10**; strength histogram: {'very_strong': 4, 'solid': 3, 'strong': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **131** words / **5.2** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 3), ('gap/background', 2), ('missing', 2)]).
- **Conclusion craft:** mean **224** words; dominant pattern: `limitations` (top [('limitations', 2), ('restate contribution → limitations', 2), ('missing', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~1001 words / ~7.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~484 words / ~3.7 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~641 words / ~4.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~1157 words / ~6.9 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~430 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Information, However, Equation, There, Here, FOR PEER REVIEW, Appendix, HVAC, Number, Total, Articles, Algorithms.
- **Frequent named algorithms:** attention(9), Attention(4), CNN(4), random forest(3), Adam(3), LSTM(3), SVM(3), BERT(3).
- **Frequent dataset/benchmark cues:** dataset(8), Dataset(5), benchmark(4), Kaggle(2), kaggle(2), Mendeley(1), IEEE 2015(1), IEEE 1998(1).
- **Common sentence openings:** `To the best of knowledge no`; `Information doi FOR PEER REVIEW www`; `In the literature various techniques have`; `The goal of each technique was`; `Researchers have addressed the issue with`; `To the best of our knowledge`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## mdpi-machines

- Deep sample: **n=8** PDFs under `fulltext_by_journal/mdpi-machines/`.
- **Length:** pages mean/median **28.0/22.5** (range 11–56); words mean/median **10077/8558**.
- **Structure:** sections mean **20.5**; paragraphs mean **47.8**; words/paragraph mean/median **252.0/147.7**.
- **Artifacts:** formulas≈**19.2**; figures≈**13.8**; tables≈**4.0**; block-diagrams≈**1.4** (mentions). Block-diagram sections: other×5, method×2, experiment×2, 3.2 CLSTM×1, 4.3 General procedure of the proposed mo×1, 5 Results×1.
- **Experiment load:** datasets mentioned≈**1.4**/paper; named algorithms≈**3.4**/paper; baseline signal **8/8**; ablation/sensitivity **0/8**; strength histogram: {'very_strong': 4, 'solid': 2, 'strong': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 8}).
- **Abstract craft:** mean **208** words / **8.9** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 2), ('gap/background → method claim → quantitative result', 2), ('gap/background → quantitative result', 1)]).
- **Conclusion craft:** mean **207** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 3), ('missing', 2), ('restate contribution → limitations', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~1308 words / ~8.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~503 words / ~3.7 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~463 words / ~3.5 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~883 words / ~6.5 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Therefore, Machines, However, Moreover, Furthermore, Additionally, IEEE, Finally, Equation, Since, Proceedings, MobileNet.
- **Frequent named algorithms:** attention(5), CNN(3), Kalman(3), Adam(2), SVM(2), GA(2), adam(1), LSTM(1).
- **Frequent dataset/benchmark cues:** dataset(4), Dataset(2), DATASET(1), NREL(1), data set(1), IEEE 
112(1), IEEE 112(1).
- **Common sentence openings:** `Local Motion Planner for Autonomous Navigation`; `Autonomous agricul- tural eld machines have`; `Nevertheless achieving suf cient autonomous navigation`; `In this context this study presents`; `The rst algorithm makes use of`; `Concurrently second back-up algorithm based on`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## mdpi-remote-sensing

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-remote-sensing/`.
- **Length:** pages mean/median **27.8/28.5** (range 13–44); words mean/median **10377/11119**.
- **Structure:** sections mean **18.5**; paragraphs mean **58.4**; words/paragraph mean/median **292.8/148.6**.
- **Artifacts:** formulas≈**11.8**; figures≈**9.4**; tables≈**3.8**; block-diagrams≈**0.9** (mentions). Block-diagram sections: introduction×2, 1 Introduction×2, back×2, References×2, other×2, conclusion×1.
- **Experiment load:** datasets mentioned≈**2.1**/paper; named algorithms≈**1.9**/paper; baseline signal **8/10**; ablation/sensitivity **0/10**; strength histogram: {'strong': 7, 'solid': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **187** words / **7.9** sentences; dominant pattern: `quantitative result` (top patterns [('quantitative result', 3), ('missing', 3), ('gap/background', 1)]).
- **Conclusion craft:** mean **250** words; dominant pattern: `limitations` (top [('limitations', 4), ('short wrap-up', 3), ('missing', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~948 words / ~6.8 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~470 words / ~3.5 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~441 words / ~3.3 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~585 words / ~4.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Remote Sens, Basel, Author, Page, Gaussian, RMSE, NDVI, However, July, NASA Author Manuscript NASA, Author Manuscript NASA Author, Manuscript.
- **Frequent named algorithms:** Random Forest(4), random forest(4), GA(3), Random forest(2), random 
forest(2), Adam(1), SVM(1), XGboost(1).
- **Frequent dataset/benchmark cues:** dataset(9), data set(4), Dataset(2), open data(2), Data Set(1), Data
set(1), benchmark(1), Open Data(1).
- **Common sentence openings:** `NASA Author Manuscript NASA Author Manuscript`; `NASA Public Access Author manuscript Remote`; `Published in final edited form as`; `Author manuscript available in PMC September`; `Europe PMC Funders Author Manuscripts Europe`; `How Universal Is the Relationship between`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## mdpi-symmetry

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-symmetry/`.
- **Length:** pages mean/median **28.8/21.0** (range 14–87); words mean/median **14936/5756**.
- **Structure:** sections mean **23.0**; paragraphs mean **100.3**; words/paragraph mean/median **145.3/145.6**.
- **Artifacts:** formulas≈**74.2**; figures≈**6.0**; tables≈**1.4**; block-diagrams≈**0.0** (mentions). Block-diagram sections: rarely lexicalized.
- **Experiment load:** datasets mentioned≈**0.5**/paper; named algorithms≈**1.3**/paper; baseline signal **6/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 3, 'moderate': 4, 'thin': 2, 'very_strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 8, 'mixed': 2}).
- **Abstract craft:** mean **103** words / **4.3** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 7), ('missing', 2), ('gap/background', 1)]).
- **Conclusion craft:** mean **212** words; dominant pattern: `restate contribution` (top [('restate contribution', 3), ('limitations', 2), ('short wrap-up', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~843 words / ~6.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~689 words / ~5.0 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~564 words / ~4.0 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~376 words / ~2.6 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Symmetry, Basel, Author, Page, Theorem, Author Manuscript Author Manuscript, PubMed, However, Phys, Planck, Refs, Lett.
- **Frequent named algorithms:** attention(4), GA(3), Ga(2), gA(1), Adam(1), Bert(1), bert(1).
- **Frequent dataset/benchmark cues:** dataset(2), Dataset(1), benchmark(1), data set(1).
- **Common sentence openings:** `Author Manuscript Author Manuscript Author Manuscript`; `NIST Author Manuscript NIST Author Manuscript`; `Spontaneous Symmetry Breaking and Nambu Goldstone`; `focus on manifestations of spontaneously broken`; `Topics covered include Introduction to the`; `Speci examples in both relativistic and`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## nature-scientific-reports

- Deep sample: **n=10** PDFs under `fulltext_by_journal/nature-scientific-reports/`.
- **Length:** pages mean/median **12.7/12.0** (range 7–25); words mean/median **7270/6774**.
- **Structure:** sections mean **8.7**; paragraphs mean **48.3**; words/paragraph mean/median **145.7/145.6**.
- **Artifacts:** formulas≈**35.7**; figures≈**20.8**; tables≈**0.8**; block-diagrams≈**0.2** (mentions). Block-diagram sections: experiment×1, Results×1.
- **Experiment load:** datasets mentioned≈**0.8**/paper; named algorithms≈**0.5**/paper; baseline signal **7/10**; ablation/sensitivity **0/10**; strength histogram: {'moderate': 2, 'solid': 7, 'strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 7, 'mixed': 3}).
- **Abstract craft:** mean **0** words / **0.0** sentences; dominant pattern: `missing` (top patterns [('missing', 10)]).
- **Conclusion craft:** mean **37** words; dominant pattern: `missing` (top [('missing', 8), ('short wrap-up', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~628 words / ~4.0 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~741 words / ~5.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~847 words / ~6.2 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~449 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** However, Phys, Scientific  RepoRts, Golgi, After, Supplementary Fig, Brazil, PbI3, TiO2, CH3NH3, Aldrich, MeOTAD.
- **Frequent named algorithms:** attention(4), SVM(1).
- **Frequent dataset/benchmark cues:** benchmark(2), dataset(2), NREL(1), BenchMark(1), data set(1), Benchmark(1).
- **Common sentence openings:** `Lead Iodide Perovskite Sensitized All-Solid-State Submicron`; `Moser Michael Gra tzel2 Nam-Gyu Park`; `We report on solid-state mesoscopic heterojunction`; `The perovskite NPs were produced by`; `Illumination with standard AM-1 sunlight generated`; `Femto second laser studies combined with`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## peerj-computer-science

- Deep sample: **n=10** PDFs under `fulltext_by_journal/peerj-computer-science/`.
- **Length:** pages mean/median **23.4/23.0** (range 8–37); words mean/median **8822/8730**.
- **Structure:** sections mean **12.4**; paragraphs mean **59.9**; words/paragraph mean/median **145.5/144.2**.
- **Artifacts:** formulas≈**17.7**; figures≈**5.7**; tables≈**2.2**; block-diagrams≈**0.5** (mentions). Block-diagram sections: other×2, experiment×2, method×2, back×1, REFERENCES×1, 3.1 Message Passing×1.
- **Experiment load:** datasets mentioned≈**2.2**/paper; named algorithms≈**2.0**/paper; baseline signal **4/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 4, 'thin': 2, 'strong': 1, 'moderate': 1, 'very_strong': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'algorithm_innovation': 1}).
- **Abstract craft:** mean **211** words / **9.7** sentences; dominant pattern: `gap/background → quantitative result` (top patterns [('gap/background → quantitative result', 2), ('method claim', 2), ('descriptive', 2)]).
- **Conclusion craft:** mean **155** words; dominant pattern: `limitations` (top [('limitations', 3), ('missing', 3), ('restate contribution → limitations → future work', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~1717 words / ~12.6 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~500 words / ~4.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~1459 words / ~10.3 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~1179 words / ~8.4 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~306 words / ~2.5 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** PeerJ Comput, Wang, United States, Zhang, Full-size
 DOI, Step, Data, However, Court, Convention, Circumstances, Aletras.
- **Frequent named algorithms:** attention(4), SVM(2), Adam(2), GA(1), Attention(1), CNN(1), GRU(1), LSTM(1).
- **Frequent dataset/benchmark cues:** dataset(8), data set(3), benchmark(3), Dataset(3), Benchmark(1), uci(1), IEEE 104(1), UCI(1).
- **Common sentence openings:** `Distributed under Creative Commons CC-BY OPEN`; `Submitted August Accepted December Published January`; `We also observe that the topical`; `eprints whiterose ac uk https eprints`; `White Rose Research Online URL for`; `This licence allows you to distribute`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## springer-discover-computing

- Deep sample: **n=10** PDFs under `fulltext_by_journal/springer-discover-computing/`.
- **Length:** pages mean/median **24.1/24.5** (range 8–39); words mean/median **10155/10288**.
- **Structure:** sections mean **20.6**; paragraphs mean **21.7**; words/paragraph mean/median **784.5/782.1**.
- **Artifacts:** formulas≈**29.0**; figures≈**9.3**; tables≈**5.3**; block-diagrams≈**2.0** (mentions). Block-diagram sections: other×10, experiment×2, 3.3 Feature selection×1, 4.4 Experimental analysis×1, 15 End if×1, 4 End for×1.
- **Experiment load:** datasets mentioned≈**2.5**/paper; named algorithms≈**5.6**/paper; baseline signal **9/10**; ablation/sensitivity **1/10**; strength histogram: {'very_strong': 5, 'thin': 1, 'moderate': 1, 'strong': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **201** words / **9.5** sentences; dominant pattern: `gap/background` (top patterns [('gap/background', 4), ('gap/background → method claim → quantitative result', 2), ('method claim → quantitative result', 1)]).
- **Conclusion craft:** mean **164** words; dominant pattern: `missing` (top [('missing', 3), ('short wrap-up', 2), ('limitations', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~778 words / ~5.7 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~1105 words / ~7.9 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~512 words / ~3.8 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~527 words / ~3.7 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~428 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Discover Computing, Additionally, Page, However, LSTM, Furthermore, GANs, Here, Number, RNNs, AI-driven, RoBERTa.
- **Frequent named algorithms:** CNN(6), attention(6), SVM(5), LSTM(4), transformer(4), Transformer(3), Attention(2), BiLSTM(2).
- **Frequent dataset/benchmark cues:** benchmark(7), dataset(7), Dataset(5), UCI(2), Benchmark(1), data set(1), kaggle(1), IEEE 802(1).
- **Common sentence openings:** `Open Access This article is licensed`; `The images or other third party`; `If material is not included in`; `You do not have permission under`; `To view copy of this licence`; `With the increasing availability of online`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## tsp-cmc

- Deep sample: **n=10** PDFs under `fulltext_by_journal/tsp-cmc/`.
- **Length:** pages mean/median **20.0/18.5** (range 14–32); words mean/median **5584/5168**.
- **Structure:** sections mean **13.9**; paragraphs mean **39.1**; words/paragraph mean/median **141.4/142.6**.
- **Artifacts:** formulas≈**13.7**; figures≈**5.9**; tables≈**4.2**; block-diagrams≈**1.7** (mentions). Block-diagram sections: other×8, experiment×2, 4 DatasetsandExperiments×1, 2 ContributionandScope×1, 4.7 PromptEngineeringStrategies×1, 5 ExperimentalSetup×1.
- **Experiment load:** datasets mentioned≈**2.2**/paper; named algorithms≈**5.7**/paper; baseline signal **9/10**; ablation/sensitivity **5/10**; strength histogram: {'very_strong': 6, 'solid': 1, 'strong': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **152** words / **5.9** sentences; dominant pattern: `gap/background` (top patterns [('gap/background', 2), ('gap/background → method claim → quantitative result', 2), ('gap/background → quantitative result', 2)]).
- **Conclusion craft:** mean **203** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 4), ('restate findings', 3), ('limitations', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~596 words / ~4.3 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~842 words / ~6.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~179 words / ~1.7 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~502 words / ~3.9 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~462 words / ~3.4 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** ComputMaterContin, LLMs, China, However, BERT, Therefore, Specifically, F1-score, Zhang, XGBoost, Wang, Thus.
- **Frequent named algorithms:** BERT(5), CNN(5), attention(5), transformer(5), LSTM(5), Transformer(3), Adam(3), BiLSTM(3).
- **Frequent dataset/benchmark cues:** dataset(10), Dataset(5), benchmark(3), data set(1), Kaggle(1), kaggle(1), Benchmark(1).
- **Common sentence openings:** `This study investigates how text classification`; `Focusing on significant challenge in the`; `The adopted methodology encompasses comprehensive approach`; `Experiments conducted on text datasets in`; `The results indicate that the integration`; `Contributions of this work include the`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

## wiley-ccpe

- Deep sample: **n=10** PDFs under `fulltext_by_journal/wiley-ccpe/`.
- **Length:** pages mean/median **17.7/17.5** (range 9–27); words mean/median **5842/4517**.
- **Structure:** sections mean **22.7**; paragraphs mean **34.7**; words/paragraph mean/median **197.4/143.2**.
- **Artifacts:** formulas≈**20.8**; figures≈**6.1**; tables≈**2.7**; block-diagrams≈**1.8** (mentions). Block-diagram sections: other×8, 3.2 Overall system architecture×1, method×1, 3.1 Featureselectioninslavenodesusingpro×1, 2 ANALYSING LCLS DATA AT NERSC×1, 2.1 Transferring Data to NERSC×1.
- **Experiment load:** datasets mentioned≈**1.2**/paper; named algorithms≈**2.0**/paper; baseline signal **5/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 5, 'very_strong': 1, 'moderate': 2, 'thin': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'mixed': 1}).
- **Abstract craft:** mean **33** words / **1.5** sentences; dominant pattern: `missing` (top patterns [('missing', 6), ('descriptive', 1), ('gap/background', 1)]).
- **Conclusion craft:** mean **150** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 7), ('restate contribution', 2), ('restate contribution → limitations → future work', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~533 words / ~3.9 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~453 words / ~3.5 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~205 words / ~1.6 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~610 words / ~4.7 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~126 words / ~1.5 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** COVID-19, Therefore, Here, Furthermore, However, According, Moreover, Hence, SPRINT, September, Copyright, John Wiley.
- **Frequent named algorithms:** CNN(3), Adam(2), SGD(2), attention(2), Random Forest(1), random forest(1), ADAM(1), ResNet(1).
- **Frequent dataset/benchmark cues:** dataset(6), benchmark(4), Dataset(1), data set(1).
- **Common sentence openings:** `Exper DOI cpe PARALLEL PERMUTATION TESTING`; `CONCURRENCY AND COMPUTATION PRACTICE AND EXPERIENCE`; `Exper Published online June in Wiley`; `DOI cpe SPECIAL ISSUE PAPER Optimization`; `Sloan1 Muriel Mewissen2 Thorsten Forster2 Michal`; `The amount of data produced by`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.
