import copy,json,tempfile,unittest
from pathlib import Path
from decimal import Decimal
from journal_rankings import calculate,decode,write_outputs,InputError

def manuscript(i,s,j='EN',version='C11'):return dict(id=i,journal=j,version=version,score=s)
def ref(i,s,j='EN'):return dict(id=i,journal=j,score=s)
def case(m,r):return dict(assessment_id='fixed-seat',rubric_id='frozen-v3',manuscripts=m,references=r)
def row(result,i,j='EN'):return next(x for x in result['rows']if x['id']==i and x['journal']==j)

class JournalRanks(unittest.TestCase):
    def test_companion_improvement_does_not_erase_p1(self):
        refs=[ref('A','83.0'),ref('B','82.4')]
        m=[manuscript('P1','83.2'),manuscript('P2','82.0'),manuscript('P3','84.4'),manuscript('P4','84.4'),manuscript('P5','82.2'),manuscript('P6','84.8')]
        a=calculate(case(m,refs));m=copy.deepcopy(m);m[1].update(score='86.6',version='C12');m[4].update(score='84.8',version='C12');b=calculate(case(m,refs))
        p,q=row(a,'P1'),row(b,'P1');self.assertEqual(p['score'],q['score']);self.assertEqual(p['version'],q['version'])
        self.assertEqual(p['ranks']['individual'],q['ranks']['individual'])
        self.assertEqual((p['ranks']['within_batch']['best'],q['ranks']['within_batch']['best']),(4,6))
        self.assertNotEqual(p['ranks']['joint']['comparison_set_id'],q['ranks']['joint']['comparison_set_id'])
    def test_tie_crossing_top3(self):
        p=case([manuscript('P2',86.6),manuscript('P5',84.8),manuscript('P6',84.8)],[ref('EL04',84.8)])
        q=row(calculate(p),'P5')['ranks']['joint'];self.assertEqual((q['best'],q['worst'],q['n']),(2,4,4));self.assertFalse(q['worst_within_top_k'])
    def test_unknown_reference_not_zero_or_imputed(self):
        q=row(calculate(case([manuscript('P1',83.2)],[ref('A',82.8),ref('X',None)])),'P1')
        self.assertEqual(q['reference_unknown_ids'],['X']);r=q['ranks']['individual'];self.assertEqual((r['best'],r['worst'],r['n']),(1,1,2));self.assertEqual(r['full_reference_roster_bounds']['worst'],2);self.assertEqual(r['full_reference_roster_bounds']['n'],3)
    def test_no_reference_pool_is_not_topk_claim(self):
        q=row(calculate(case([manuscript('P1',90)],[ref('unknown',None)])),'P1');self.assertIsNone(q['ranks']['individual']['worst_within_top_k']);self.assertIsNone(q['ranks']['joint']['worst_within_top_k']);self.assertTrue(q['ranks']['within_batch']['worst_within_top_k'])
    def test_decimal_comparison(self):
        q=row(calculate(case([manuscript('P1','83.20000000000000000001')],[ref('A','83.2')])),'P1');self.assertEqual(q['ranks']['individual']['worst'],1)
    def test_journal_sets_and_versions_are_separate(self):
        p=case([manuscript('P1',80,'EN','C11'),manuscript('P1',80,'AS','C12')],[ref('A',81,'EN'),ref('A',79,'AS')]);out=calculate(p)
        self.assertEqual(row(out,'P1','EN')['ranks']['individual']['best'],2);self.assertEqual(row(out,'P1','AS')['ranks']['individual']['best'],1);self.assertEqual(row(out,'P1','AS')['version'],'C12')
    def test_set_id_order_independent(self):
        p=case([manuscript('P1',80),manuscript('P2',82)],[ref('A',81),ref('B',79)]);a=calculate(p);p['references'].reverse();p['manuscripts'].reverse();b=calculate(p)
        self.assertEqual(row(a,'P1')['ranks'],row(b,'P1')['ranks'])
    def test_colliding_ids_rejected(self):
        with self.assertRaises(InputError):calculate(case([manuscript('P1',80)],[ref('P1',81)]))
    def test_invalid_scores_rejected(self):
        for value in [True,None,'NaN','Infinity',-1,101,[],{}]:
            with self.subTest(value=value),self.assertRaises(InputError):calculate(case([manuscript('P1',value)],[]))
    def test_missing_version_rejected(self):
        p=case([manuscript('P1',80)],[]);del p['manuscripts'][0]['version']
        with self.assertRaises(InputError):calculate(p)
    def test_missing_reference_score_is_not_silent_unknown(self):
        p=case([manuscript('P1',80)],[dict(id='A',journal='EN')])
        with self.assertRaises(InputError):calculate(p)
    def test_missing_series_rejected(self):
        p=case([manuscript('P1',80)],[]);del p['rubric_id']
        with self.assertRaises(InputError):calculate(p)
    def test_invalid_k_rejected(self):
        for k in [0,-1,True,2.5]:
            with self.subTest(k=k),self.assertRaises(InputError):calculate(case([manuscript('P1',80)],[]),k)
    def test_duplicate_json_keys_and_nonfinite_json(self):
        for data in [b'{"score":80,"score":90}',b'{"score":NaN}']:
            with self.assertRaises(InputError):decode(data)
    def test_snapshot_output_cannot_be_silently_overwritten(self):
        result=calculate(case([manuscript('P1',80)],[ref('A',81)]))
        with tempfile.TemporaryDirectory()as tmp:
            write_outputs(result,tmp);p=Path(tmp)/'RANKS.json';before=p.read_bytes()
            with self.assertRaises(InputError):write_outputs(result,tmp)
            self.assertEqual(before,p.read_bytes());self.assertEqual(len(json.loads(before)['rows']),1)
    def test_unused_reference_journal_disclosed(self):
        q=calculate(case([manuscript('P1',80)],[ref('A',81,'AS')]))
        self.assertEqual(q['unused_reference_journals'],['AS'])

if __name__=='__main__':unittest.main()
