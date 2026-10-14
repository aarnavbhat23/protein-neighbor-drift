"""Encode a pinned public peptide set or local CSV; compare with composition/BOS."""
import argparse
import csv
import hashlib
import io
import json
import platform
import time
import urllib.request
from pathlib import Path
import numpy as np
from tool import analyze

MODEL = 'facebook/esm2_t6_8M_UR50D'
REVISION = 'c731040fcd8d73dceaa04b0a8e6329b345b0f5df'
SOURCE_COMMIT = 'ae676872b0aff1e6713bd3188f8cc51fd7cca651'
SOURCE_URL = f'https://raw.githubusercontent.com/aarnavbhat23/amp-top100-atlas/{SOURCE_COMMIT}/top100_audit.csv'
AA = 'ACDEFGHIKLMNPQRSTVWY'

def composition(sequence):
    if not sequence or not set(sequence) <= set(AA):
        raise ValueError('Require nonempty canonical uppercase sequence')
    return [sequence.count(a)/len(sequence) for a in AA]

def mean_residues(hidden, attention, special):
    """Exclude BOS, EOS, special tokens and padding from mean pooling."""
    mask = attention.bool() & ~special.bool()
    if not mask.any(dim=1).all():
        raise ValueError('No residues available to pool')
    return (hidden * mask.unsqueeze(-1)).sum(dim=1)/mask.sum(dim=1).unsqueeze(-1)

def main():
    import torch
    import transformers
    from transformers import AutoModel, AutoTokenizer
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,help='CSV with sequence and optional id/rank columns; otherwise uses pinned public atlas')
    p.add_argument('--output-dir',type=Path,default=Path('results/esm-public-atlas'))
    p.add_argument('--device',choices=['cpu','cuda','mps'],default='cpu')
    p.add_argument('--reference',choices=['composition','bos'],default='composition')
    p.add_argument('--batch-size',type=int,default=16)
    p.add_argument('--k',type=int,default=10)
    args=p.parse_args()
    if args.batch_size < 1:
        p.error('batch-size must be positive')
    raw=args.input.read_bytes() if args.input else urllib.request.urlopen(SOURCE_URL,timeout=60).read()
    records=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    if not 1 <= args.k < len(records):
        p.error('Require 1 <= k < sequence count')
    sequences=[r['sequence'] for r in records]
    for seq in sequences:
        composition(seq)
        if len(seq)>1022:
            p.error('Sequence exceeds model limit; silent truncation is disallowed')
    torch.manual_seed(0)
    if args.device=='cpu':
        torch.set_num_threads(4)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    model=AutoModel.from_pretrained(MODEL,revision=REVISION,add_pooling_layer=False).to(args.device).eval()
    output=[]
    started=time.perf_counter()
    with torch.inference_mode():
        for start in range(0,len(records),args.batch_size):
            seqs=sequences[start:start+args.batch_size]
            encoded=tokenizer(seqs,padding=True,return_tensors='pt',return_special_tokens_mask=True,truncation=False)
            special=encoded.pop('special_tokens_mask').to(args.device)
            encoded={k:v.to(args.device) for k,v in encoded.items()}
            hidden=model(**encoded).last_hidden_state
            mean=mean_residues(hidden,encoded['attention_mask'],special).cpu().numpy()
            bos=hidden[:,0].cpu().numpy()
            for j,seq in enumerate(seqs):
                r=records[start+j]
                item={'id':str(r.get('id') or r.get('rank') or f'sequence-{start+j+1}'),
                      'sequence':seq,'reference':composition(seq) if args.reference=='composition' else bos[j].tolist(),
                      'candidate':mean[j].tolist()}
                if r.get('family'):
                    item['family']=r['family']
                output.append(item)
    elapsed=time.perf_counter()-started
    data={'data_kind':'real pretrained-model embeddings on supplied sequences; activity not evaluated',
          'k':args.k,'rows':output}
    report=analyze(data)
    manifest={'model':MODEL,'revision':REVISION,'source':str(args.input) if args.input else SOURCE_URL,
              'source_commit':None if args.input else SOURCE_COMMIT,
              'source_sha256':hashlib.sha256(raw).hexdigest(),'n_sequences':len(records),
              'reference':args.reference,'candidate':'final-layer residue mean excluding special tokens and padding',
              'device':args.device,'batch_size':args.batch_size,'inference_wall_seconds':elapsed,
              'python':platform.python_version(),'torch':torch.__version__,'transformers':transformers.__version__,
              'numpy':np.__version__,'seed':0,
              'interpretation':'This candidate-selected set has no experimental family/activity labels. Neighbor change does not establish that ESM is better. Timing excludes weight load and includes tokenization, pooling and CPU transfer; not a standardized serving benchmark.'}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,content in [('input.json',data),('report.json',report),('manifest.json',manifest)]:
        (args.output_dir/name).write_text(json.dumps(content,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'n_sequences':len(records),'mean_neighbor_overlap':report['mean_neighbor_overlap'],'inference_seconds':elapsed}))

if __name__=='__main__':
    main()
