"""Plot observed neighbor overlap; no activity or superiority claims."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',type=Path,default=Path('results/esm-public-atlas'))
    args=p.parse_args()
    data=json.loads((args.results/'input.json').read_text())
    report=json.loads((args.results/'report.json').read_text())
    rows={r['id']:r for r in data['rows']}
    overlap=np.array([r['neighbor_overlap'] for r in report['records']])
    lengths=[len(rows[r['id']]['sequence']) for r in report['records']]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    bins=np.arange(-.05,1.06,.1)
    axes[0].hist(overlap,bins=bins,color='#197875',edgecolor='white')
    axes[0].axvline(overlap.mean(),color='#c55331',linestyle='--',label=f'Mean: {overlap.mean():.1%}')
    axes[0].set(xlim=(-.05,1.05),xlabel='Shared fraction of top-10 neighbors',ylabel='Peptides')
    axes[0].legend(frameon=False)
    axes[1].scatter(lengths,overlap,alpha=.65,s=28,color='#197875')
    axes[1].set(xlabel='Peptide length (residues)',ylabel='Shared fraction of top-10 neighbors',ylim=(-.05,1.05))
    fig.suptitle('Amino-acid composition vs ESM-2 mean embeddings',fontweight='bold')
    fig.supxlabel('100 public candidate peptides; representation sensitivity, not activity validation',fontsize=9)
    for extension in ('png','svg'):
        fig.savefig(args.results/f'neighbor-overlap.{extension}',dpi=220)
    plt.close(fig)

if __name__=='__main__':
    main()
