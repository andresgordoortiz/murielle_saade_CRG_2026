# Murielle Saade RNA-seq

Nine independent samples: WT, KO3 and KO25, three replicates each. Human, reverse-stranded, paired-end 150 bp; both pipelines use **GRCh38/hg38**.

From the cluster checkout:

```bash
git pull
bash scripts/submit.sh
```

The submitter uses Bash only. Paste the Seqera token at the hidden prompt; an existing `TOWER_ACCESS_TOKEN` skips the prompt. Jobs load `Nextflow`, `Java`, `Singularity/4.0.2` and `Python`.

Inputs and paths:

- FASTQs: `raw_data_2026/WT_1_1.fq.gz`, `WT_1_2.fq.gz`, etc., directly inside the repo.
- Sample inputs: `samples/rnaseq.csv`, `samples/metadata.tsv` and `samples/SHA256SUMS`.
- Existing VAST workflow: `/users/aaljord/agordo/git/vast-tools_nextflow`.
- Existing database: `/users/aaljord/agordo/VASTDB/Hs2`. It is validated, **never downloaded**.
- Work: `/nfs/scratch01/aaljord/agordo/murielle_saade_CRG_2026/work_rnaseq` and `work_vast`.
- Override site paths in `config/cluster.env` if necessary.

Submission queues reference preparation, nf-core/rnaseq 3.27.0, then VAST. Existing Ensembl FASTA/GTF files are reused. Failed jobs prevent their dependents from starting; cancel old pending jobs before submitting a replacement chain.

Outputs inside this repo:

- `results/rnaseq/`: STAR/Salmon count tables, alignments and QC.
- `results/vast/inclusion_tables/murielle_saade_2026_INCLUSION_LEVELS_FULL-hg38.tab`: inclusion table.
- `logs/`: Slurm logs; `runs/`: Nextflow state for resuming.

VAST receives both mates from nf-core's saved trimmed reads. Its working copy fixes mouse-only junction filters without modifying the shared workflow. Comparisons are disabled for this inclusion-table run; `compare --paired` refers to matched biological replicates, not paired-end reads. Expression count tables are produced for downstream DE analysis; statistical DE tests are not run here.

Raw reads, results, references and runtime files are excluded from Git. Full execution and site-module availability require verification on CRG.
