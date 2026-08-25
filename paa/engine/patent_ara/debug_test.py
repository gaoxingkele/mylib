import sys
sys.path.insert(0, '.')

from patent_ara import PatentParser, ElementVerdict, Evaluator
from tests.test_patent_ara import CN_FULL

ara = PatentParser(lang='zh').parse(CN_FULL)
print('Claims:', [(c.number, len(c.elements)) for c in ara.claims])
for c in ara.claims:
    for e in c.elements:
        print(f'  {e.id}: {e.element_type} {e.text[:50]}')

verdicts = []
for c in ara.claims:
    for e in c.elements:
        status = 'not_disclosed' if e.id == 'C1.E4' else 'disclosed'
        verdicts.append(ElementVerdict(element_id=e.id, reference_id='R1', status=status))

for e in ara.claims[2].elements:
    verdicts.append(ElementVerdict(element_id=e.id, reference_id='R2', status='disclosed'))

report = Evaluator(ara).evaluate(verdicts)
for r in report['claims']:
    print(f"Claim {r['number']}: novel={r['novel']} anticipated_by={r['anticipated_by']} score={r['claim_score']}")
