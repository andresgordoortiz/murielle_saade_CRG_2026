# Murielle Saade RNA-seq

Nine independent samples: WT, KO3 and KO25, three replicates each. Human, reverse-stranded, paired-end 150 bp; both pipelines use **GRCh38/hg38**.

From the cluster checkout:

```bash
git pull
bash scripts/submit.sh
```

To rerun only VAST using completed RNA-seq trimmed reads: `bash scripts/submit.sh vast`.

For betAS on the finished inclusion table: `bash scripts/submit.sh betas` (no Seqera token needed). This submits three independent array tasks: WT vs KO3, WT vs KO25 and KO3 vs KO25, each with one CPU, 64 GB and 48 hours. It reuses the installed R 4.5.2/betAS environment in `/users/aaljord/agordo/git/maria_MH_Adel_spire12ko_2026`; nothing is installed. Temporary files use scratch.

betAS outputs are under `results/betas/CONTRAST/`: `all_events.csv`, `differential.csv`, `combination.csv`, filtered inputs and statistical checkpoints. Filtering requires complete PSI and N≥10 in each of that contrast's six samples; all event types are retained. Settings match the reference run: 500 points, 1,000 simulations, fixed seed, no coverage weighting. Positive delta means higher inclusion in the second group. Differential selection uses upstream `FDR`≤0.05 and |delta|≥0.10; combination adds Pdiff≥0.95. Upstream `FDR` is an empirical per-event false-positive rate, not BH-adjusted FDR. Resubmitting `betas` reuses completed stages after checking inputs/settings; `COMPLETE` marks finished CSV exports.

Numeric PSI and finite, nonnegative inclusion/exclusion counts are validated before betAS filtering. Invalid/missing values are excluded and recorded in `excluded_invalid_values.tsv` and `filter_qc.csv`; the original inclusion table is unchanged.

The submitter uses Bash only. Paste the Seqera token at the hidden prompt; an existing `TOWER_ACCESS_TOKEN` skips the prompt. Jobs use the system `singularity` executable and load `Nextflow`, `Java` and `Python/3.12.3-GCCcore-13.2.0`.

Inputs and paths:

- FASTQs: `raw_data_2026/WT_1_1.fq.gz`, `WT_1_2.fq.gz`, etc., directly inside the repo.
- Sample inputs: `samples/rnaseq.csv`, `samples/metadata.tsv` and `samples/SHA256SUMS`.
- Existing VAST workflow: `/users/aaljord/agordo/git/vast-tools_nextflow`.
- Existing database: `/users/aaljord/agordo/VASTDB/Hs2`. It is validated, **never downloaded**.
- Existing genome/GTF: `references/ensembl115_GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz` and `Homo_sapiens.GRCh38.115.gtf.gz`.
- Work: `/nfs/scratch01/aaljord/agordo/murielle_saade_CRG_2026/work_rnaseq` and `work_vast`.
- Override site paths in `config/cluster.env` if necessary.

Submission validates the existing Hs2, genome and GTF, prints their paths, then queues nf-core/rnaseq 3.27.0 and VAST. There is no reference-download job or download command. Missing files stop submission with their exact paths; change `REFERENCE_DIR` to use files stored elsewhere. Failed jobs prevent their dependents from starting; cancel old pending jobs before submitting a replacement chain.

Outputs inside this repo:

- `results/rnaseq/`: STAR/Salmon count tables, alignments and QC.
- `results/vast/inclusion_tables/murielle_saade_2026_INCLUSION_LEVELS_FULL-hg38.tab`: inclusion table.
- `logs/`: Slurm logs; `runs/`: Nextflow state for resuming.

VAST receives both mates from nf-core's saved trimmed reads. Its working copy fixes mouse-only junction filters without modifying the shared workflow. Comparisons are disabled for this inclusion-table run; `compare --paired` refers to matched biological replicates, not paired-end reads. Expression count tables are produced for downstream DE analysis; statistical DE tests are not run here.

Raw reads, results, references and runtime files are excluded from Git. Full execution and site-module availability require verification on CRG.
