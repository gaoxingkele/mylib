"""Rank frozen manuscript scores against fixed references; no score generation.

Input JSON: {assessment_id, rubric_id,
 manuscripts:[{id,journal,version,score}],
 references:[{id,journal,score}]}.
Scores accept decimal strings or JSON numbers in [0,100]; only references may
have score:null. IDs are unique within each journal across both roles. Every
manuscript has its own version. One payload declares one comparable assessment
series and scale; this program cannot verify that scientific comparability.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from decimal import Decimal,InvalidOperation
from pathlib import Path

class InputError(ValueError):pass
def token(value,field):
    if not isinstance(value,str)or not value.strip():raise InputError(field+' must be a nonempty string')
    return value.strip()
def number(value,nullable=False):
    if value is None and nullable:return None
    if isinstance(value,bool)or not isinstance(value,(int,float,str,Decimal)):raise InputError('score must be a decimal in [0,100]')
    try:s=Decimal(str(value))
    except InvalidOperation as exc:raise InputError('invalid decimal score')from exc
    if not s.is_finite()or not 0<=s<=100:raise InputError('score must be finite and in [0,100]')
    return s
def text(s):return None if s is None else format(s.normalize(),'f')
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
def normalized(payload):
    if not isinstance(payload,dict):raise InputError('input must be an object')
    context={k:token(payload.get(k),k)for k in ['assessment_id','rubric_id']}
    result={};seen=set()
    for role in ['manuscripts','references']:
        values=payload.get(role)
        if not isinstance(values,list)or (role=='manuscripts'and not values):raise InputError(role+' must be a list; manuscripts cannot be empty')
        out=[]
        for v in values:
            if not isinstance(v,dict):raise InputError(role+' entries must be objects')
            if 'score'not in v:raise InputError('score key is required; use explicit null for an unknown reference')
            p={k:token(v.get(k),k)for k in ['id','journal']};key=(p['journal'],p['id'])
            if key in seen:raise InputError('duplicate/colliding journal ID: '+str(key))
            seen.add(key);p['version']=token(v.get('version'),'version')if role=='manuscripts'else v.get('version')
            if p['version']is not None and not isinstance(p['version'],str):raise InputError('reference version must be a string or null')
            p['score']=number(v.get('score'),nullable=role=='references');p['role']=role;out.append(p)
        result[role]=out
    return context,result['manuscripts'],result['references']
def known_rank(item,others,scope,context,top_k):
    values=[x['score']for x in others];score=item['score']
    best=1+sum(x>score for x in values);worst=1+sum(x>=score for x in values)
    members=sorted([dict(id=x['id'],role=x['role'],version=x['version'],score=text(x['score']))for x in others+[item]],key=lambda x:(x['role'],x['id']))
    return dict(best=best,worst=worst,n=len(values)+1,top_k=top_k,worst_within_top_k=worst<=top_k,comparison_set_id=digest(dict(**context,journal=item['journal'],scope=scope,members=members)))
def calculate(payload,top_k=3):
    if type(top_k)is not int or top_k<=0:raise InputError('top_k must be a positive integer')
    context,manuscripts,references=normalized(payload);rows=[];rosters={}
    for j in sorted({x['journal']for x in manuscripts}):
        m=[x for x in manuscripts if x['journal']==j];rr=[x for x in references if x['journal']==j];known=[x for x in rr if x['score']is not None];unknown=[x['id']for x in rr if x['score']is None]
        for item in sorted(m,key=lambda x:x['id']):
            others=[x for x in m if x['id']!=item['id']]
            ranks={scope:known_rank(item,group,scope,context,top_k)for scope,group in [('individual',known),('within_batch',others),('joint',known+others)]}
            for scope in ['individual','joint']:
                q=ranks[scope]
                q['full_reference_roster_bounds']=dict(best=q['best'],worst=q['worst']+len(unknown),n=q['n']+len(unknown),unknown_count=len(unknown),qualification='Algebraic bound, not an imputed score')
                if not known:q['worst_within_top_k']=None
            rows.append(dict(id=item['id'],journal=j,version=item['version'],score=text(item['score']),reference_complete_n=len(known),reference_unknown_ids=sorted(unknown),reference_status='COMPLETE_SCORED_SUBSET'if known else'NO_COMPLETE_REFERENCES',ranks=ranks))
        roster=[]
        for item in known+m:
            others=[x for x in known+m if x['id']!=item['id']]
            q=known_rank(item,others,'joint',context,top_k)
            roster.append(dict(id=item['id'],role=item['role'],version=item['version'],score=text(item['score']),best=q['best'],worst=q['worst'],n=q['n'],comparison_set_id=q['comparison_set_id']))
        rosters[j]=sorted(roster,key=lambda x:(-Decimal(x['score']),x['id']))
    return dict(schema='journal_rankings/1',**context,scope='Arithmetic on supplied comparable frozen scores; not a manuscript review or acceptance model',rows=rows,journal_rosters=rosters,unused_reference_journals=sorted({x['journal']for x in references}-{x['journal']for x in manuscripts}))
def no_duplicates(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise InputError('duplicate JSON key: '+k)
        result[k]=v
    return result
def decode(raw):
    return json.loads(raw.decode('utf-8-sig'),parse_float=Decimal,parse_constant=lambda s:(_ for _ in ()).throw(InputError('nonfinite JSON number: '+s)),object_pairs_hook=no_duplicates)
def load(path):return decode(Path(path).read_bytes())
def rank_label(q):return (str(q['best'])if q['best']==q['worst']else f"{q['best']}–{q['worst']}")+'/'+str(q['n'])
def write_outputs(result,directory,overwrite=False):
    d=Path(directory);d.mkdir(parents=True,exist_ok=True);paths=[d/n for n in ['RANKS.json','RANKS.csv','RANKS.md']]
    if not overwrite and any(p.exists()for p in paths):raise InputError('output exists; choose a new snapshot directory or explicitly use --overwrite')
    paths[0].write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    flat=[]
    for x in result['rows']:
        row={k:x[k]for k in ['id','journal','version','score','reference_complete_n','reference_status']};row['reference_unknown_ids']=';'.join(x['reference_unknown_ids'])
        for name,q in x['ranks'].items():
            row.update({name+'_'+k:q[k]for k in ['best','worst','n','worst_within_top_k','comparison_set_id']})
        flat.append(row)
    with paths[1].open('w',encoding='utf-8-sig',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    lines=['# Fixed-sample journal ranks','','Assessment: '+result['assessment_id']+'; rubric: '+result['rubric_id']+'.','',result['scope']+'. Unknown references are excluded, never zero-imputed. Ties occupy the full interval. Each manuscript retains its own version.','']
    for scope in ['individual','within_batch','joint']:
        lines += ['## '+scope,'','|Journal|Manuscript|Version|Score|Rank / N|Unknown refs|','|---|---|---|---:|---:|---:|']
        for x in result['rows']:
            cell=rank_label(x['ranks'][scope])
            if scope!='within_batch'and x['reference_status']=='NO_COMPLETE_REFERENCES':cell+=' (no complete reference evidence)'
            lines.append('|'+ '|'.join(str(v).replace('|','\\|').replace('\n',' ')for v in [x['journal'],x['id'],x['version'],x['score'],cell,len(x['reference_unknown_ids'])])+'|')
        lines.append('')
    paths[2].write_text('\n'.join(lines),encoding='utf-8')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--top-k',type=int,default=3);ap.add_argument('--overwrite',action='store_true');args=ap.parse_args()
    try:
        if args.input.resolve()in {(args.out_dir/n).resolve()for n in ['RANKS.json','RANKS.csv','RANKS.md']}:raise InputError('input cannot be an output file')
        raw=args.input.read_bytes();result=calculate(decode(raw),args.top_k);result['input_sha256']=hashlib.sha256(raw).hexdigest();write_outputs(result,args.out_dir,args.overwrite)
    except (InputError,OSError,json.JSONDecodeError)as exc:ap.exit(2,str(exc)+'\n')
    print(f"PASS {len(result['rows'])} rows; individual / within_batch / joint; no scores generated")
if __name__=='__main__':main()
