from Bio import SeqIO
from Bio.SeqUtils import gc_fraction

with open('genomeC.fna', 'rt') as handle:
    for rec in SeqIO.parse(handle, 'fasta'):
        gc_content = gc_fraction(rec.seq)

print(gc_content)