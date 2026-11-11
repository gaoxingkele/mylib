"""Evidence-bound chapter scoring. stdlib only; does not generate judgments.

Usage: python chapter_score.py --rubric RUBRIC.json --cards review*.json
       --baseline old.json --references reference*.json --out results
"""
import argparse,csv,hashlib,json,pathlib,statistics
from fractions import Fraction as F

def unique_object(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError(f'Duplicate JSON key: {k}')
        out[k]=v
    return out

def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def validate_rubric(r):
    ds=r['dimension_weights']; ws=r['chapter_dimension_weights']; cs=r['chapter_weights']
    if sum(ds.values())!=100 or sum(cs.values())!=100: raise ValueError('Weights must total100')
    if set(ws)!=set(cs): raise ValueError('Chapter margins mismatch')
    for c,row in ws.items():
        if set(row)!=set(ds): raise ValueError('Dimension keys mismatch')
        if any(type(w) is not int or w<0 for w in row.values()): raise ValueError('Nonnegative integer weights required')
        if sum(row.values())!=cs[c]: raise ValueError('Row margin mismatch')
    for d,w in ds.items():
        if sum(row[d] for row in ws.values())!=w: raise ValueError('Column margin mismatch')
    return sum(w>0 for row in ws.values() for w in row.values())

def valid_rating(v):
    if v is not None and (type(v) is not int or not 0<=v<=5): raise ValueError('Ratings must be int0..5 or null; bool is invalid')

def score(r,card,old=None):
    validate_rubric(r)
    if set(card['chapters'])!=set(r['chapter_weights']): raise ValueError('Missing or extra chapters')
    rows=[]; points=F(0);coverage=0;count=0;delta=F(0)
    dim={d:{'points':F(0),'coverage':0,'delta':F(0)} for d in r['dimension_weights']}
    if old:
        if set(old['ratings'])!=set(r['dimension_weights']): raise ValueError('Baseline dimensions differ')
        for v in old['ratings'].values():
            valid_rating(v)
            if v is None: raise ValueError('Complete baseline required for difference')
        reconstructed=sum(F(w*old['ratings'][d],5) for d,w in r['dimension_weights'].items())
        if reconstructed!=F(str(old['score_100'])): raise ValueError('Old total does not reconstruct exactly')
    for c,wrow in r['chapter_dimension_weights'].items():
        ch=card['chapters'][c];cells=ch['cells'];expected={d for d,w in wrow.items() if w}
        if set(cells)!=expected: raise ValueError(f'{c}: missing/extra nonzero cells')
        cp=F(0);cw=0;cd=F(0)
        for d,cell in cells.items():
            v=cell['rating'];valid_rating(v);w=wrow[d];count+=1
            if v is None: continue
            p=F(w*v,5);cp+=p;cw+=w;points+=p;coverage+=w;dim[d]['points']+=p;dim[d]['coverage']+=w
            if old:
                x=F(w*(v-old['ratings'][d]),5);cd+=x;delta+=x;dim[d]['delta']+=x
        complete=cw==r['chapter_weights'][c]
        rows.append({'chapter':c,'weight':r['chapter_weights'][c],'known_weight':cw,'known_points':float(cp),
                     'score_100':float(100*cp/cw) if complete else None,'complete':complete,
                     'delta_points':float(cd) if old and complete else None})
    complete=coverage==100
    result={'paper':card['paper'],'journal':card['journal_code'],'known_points':float(points),'coverage_weight':coverage,
            'complete':complete,'score_100':float(points) if complete else None,'cell_count':count,'chapters':rows,
            'dimensions':{d:{'weight':r['dimension_weights'][d],'known_weight':x['coverage'],'known_points':float(x['points']),
                'rating_0_5':float(5*x['points']/x['coverage']) if x['coverage']==r['dimension_weights'][d] else None,
                'delta_points':float(x['delta']) if old and x['coverage']==r['dimension_weights'][d] else None} for d,x in dim.items()}}
    if old:
        result.update(old_score_100=float(reconstructed),old_counterfactual_100=float(reconstructed),
                      difference=float(points-reconstructed) if complete else None,
                      weight_change_contribution=0,delta_sum=float(delta) if complete else None)
        if complete and delta!=points-reconstructed: raise AssertionError('Delta conservation failed')
    return result

def reference_stats(files,chapters):
    refs={};groups={}
    for path in files:
        for c in read(path)['cards']:
            id=c['id']
            if id in refs: raise ValueError('Duplicate reference ID')
            refs[id]=c
            j=c.get('journal_code',c.get('journal'))
            j={'energies':'EN','electronics':'EL','applsci':'AS','ieee-access':'ACC','AC':'ACC'}.get(j,j)
            groups.setdefault(j,[]).append(c)
    out={}
    for j,cards in groups.items():
        out[j]={}
        if len(cards)!=10: raise ValueError(f'{j}: fixed10 required')
        for ch in chapters:
            vals=[];unknown=[]
            for c in cards:
                module=c['modules'][ch]
                # EN calibration explicitly calls this the reader-visible functional score.
                v=module['rating'] if 'rating' in module else module['reader_visible_quality_score'];valid_rating(v)
                if v is None: unknown.append(c['id'])
                else: vals.append(v*20)
            q=statistics.quantiles(vals,n=4,method='inclusive') if len(vals)>=2 else [None]*3
            out[j][ch]={'n':len(vals),'median_100':statistics.median(vals) if vals else None,
                        'q1_100':q[0],'q3_100':q[2],'min_100':min(vals) if vals else None,'max_100':max(vals) if vals else None,'unknown_ids':unknown}
    return refs,out

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def aggregate(rubric,files,baseline=None,references=()):
    r=read(rubric);validate_rubric(r);old={}
    if baseline:
        b=read(baseline)
        if b['weights']!=r['dimension_weights']: raise ValueError('Old dimension weights changed')
        old={(c['paper'],c['journal']):c for c in b['cards']}
    refs,stats=reference_stats(references,r['chapter_weights']) if references else ({},{})
    cards=[];seen=set()
    for path in files:
        data=read(path)
        for c in data['cards']:
            key=(c['paper'],c['journal_code'])
            if key in seen: raise ValueError('Duplicate manuscript card')
            seen.add(key)
            if not c.get('reading_scope') and not c.get('provenance'): raise ValueError('Reading scope required')
            for ch in c['chapters'].values():
                for cell in ch['cells'].values():
                    if cell['rating'] is not None and not cell.get('anchors'): raise ValueError('Evidence anchors required')
                for id in ch.get('reference_ids',[]):
                    if refs and id not in refs: raise ValueError(f'Unknown reference {id}')
                    if refs:
                        ref=refs[id];j=ref.get('journal_code',ref.get('journal'))
                        j={'energies':'EN','electronics':'EL','applsci':'AS','ieee-access':'ACC','AC':'ACC'}.get(j,j)
                        if j!=c['journal_code']: raise ValueError(f'Reference {id} not in manuscript target journal')
            s=score(r,c,old.get(key));s['raw_review_file']=str(path);s['raw_review_sha256']=sha(path)
            if stats:
                for row in s['chapters']:
                    z=stats[c['journal_code']][row['chapter']];row['reference']=z
                    row['difference_from_reference_median']=row['score_100']-z['median_100'] if row['score_100'] is not None and z['median_100'] is not None else None
            s['gates']=c.get('gates',{});s['logic_edges']=c.get('logic_edges',[]);cards.append(s)
    journal_order={j:i for i,j in enumerate(['EN','EL','AS','ACC'])}
    cards.sort(key=lambda c:(c['paper'],journal_order.get(c['journal'],len(journal_order)),c['journal']))
    return {'rubric_version':r['version'],'rubric_sha256':sha(rubric),'manuscripts_unchanged_declaration':r.get('manuscripts_unchanged'),
            'meaning':'Verify manuscript hashes externally. Under verified identical inputs, new-old is assessment refinement, not revision gain/loss. Scores are not acceptance probabilities.',
            'reference_comparison':'Functional descriptive anchors; reference one-module score differs in resolution from manuscript multi-cell score. No acceptance cutoff.',
            'input_hashes':{str(p):sha(p) for p in [rubric,*files,*references,*([baseline] if baseline else [])]},
            'reference_chapter_stats':stats,'cards':cards}

def write_outputs(result,out):
    out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'ASSESSMENT_V3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for name,rows in [('TOTAL_COMPARISON.csv',[{k:c.get(k) for k in ['paper','journal','old_score_100','score_100','difference','coverage_weight','weight_change_contribution']} for c in result['cards']]),
                      ('CHAPTER_COMPARISON.csv',[{'paper':c['paper'],'journal':c['journal'],**{k:v for k,v in x.items() if k!='reference'},**{'reference_'+k:v for k,v in x.get('reference',{}).items()}} for c in result['cards'] for x in c['chapters']]),
                      ('DIMENSION_DELTAS.csv',[{'paper':c['paper'],'journal':c['journal'],'dimension':d,**x} for c in result['cards'] for d,x in c['dimensions'].items()])]:
        with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--rubric',required=True);p.add_argument('--cards',nargs='+',required=True);p.add_argument('--baseline');p.add_argument('--references',nargs='*',default=[]);p.add_argument('--out',required=True);a=p.parse_args()
    result=aggregate(a.rubric,a.cards,a.baseline,a.references);write_outputs(result,a.out)
    print(json.dumps({'cards':len(result['cards']),'complete':sum(c['complete'] for c in result['cards']),'cells':sum(c['cell_count'] for c in result['cards'])}))
if __name__=='__main__': main()
