# Murielle Saade neural organoid RNA-seq, 2026

Nine samples: WT, KO3 and KO25, each with three independent replicates. Each sample has paired-end R1/R2 FASTQs, not two technical replicates. See [the QC report](qc/REPORT.md) for the measured species, strandedness, depth and quality. Full-file local scanning was stopped after five FASTQs following a PC overload; the remaining full QC belongs on Slurm.

Both analyses use **human GRCh38 / hg38**. VAST uses the **Hs2** library; gene quantification uses the **Ensembl 115 GRCh38 primary assembly and GTF**. The species-screen mouse GRCm39 transcriptome is only a diagnostic reference and is never passed to either analysis.

## Outputs and workflow

1. Prepare the GRCh38 references and, if missing, VASTDB Hs2.
2. Run **nf-core/rnaseq 3.27.0**, using STAR + Salmon and paired-end fastp trimming. Save the cleaned FASTQs.
3. Run your existing **vast-tools_nextflow** clone on those same cleaned pairs, with its trimming and downstream comparisons disabled.

The jobs are linked with Slurm `afterok` dependencies. A failed stage prevents its dependent job from starting. No samples are pooled or dropped by these scripts; nf-core's own low-mapping/low-read exclusion checks remain enabled and must be reviewed in MultiQC.

Requested products:

- `results/vast/inclusion_tables/murielle_saade_2026_INCLUSION_LEVELS_FULL-hg38.tab`
- `results/rnaseq/star_salmon/salmon.merged.gene_counts.tsv`
- `results/rnaseq/star_salmon/salmon.merged.gene_counts_length_scaled.tsv`
- `results/rnaseq/star_salmon/salmon.merged.gene_lengths.tsv`
- Per-sample Salmon `quant.sf`, transcript count matrices, and MultiQC under `results/rnaseq/`.

These are **expression count tables for DE**, not statistical DE results. nf-core/rnaseq does not test WT versus KO. For later DESeq2 analysis, import Salmon estimates with tximport and length offsets, or use the length-scaled counts as documented by nf-core. TPM is not a count input. [nf-core outputs](https://nf-co.re/rnaseq/3.27.0/docs/output/)

## Put the files on CRG

Keep the observed sample subdirectories:

```text
/users/aaljord/agordo/murielle_saade_collab/raw_data_2026/
  WT_1/WT_1_1.fq.gz
  WT_1/WT_1_2.fq.gz
  ...
  KO25_3/KO25_3_2.fq.gz
```

For example, from this PC, with `CRG_HOST` set to your SSH destination:

```bash
rsync -a --info=progress2 /home/andgortiz/Downloads/Murielle_Saade_API/ \
  "$CRG_HOST:/users/aaljord/agordo/murielle_saade_collab/raw_data_2026/"
```

The transfer has no deletion flag. Do not put the raw reads inside this Git repository.

## Submit on CRG

After pushing this repository to GitHub, clone it on CRG alongside the raw-data folder:

```bash
mkdir -p /users/aaljord/agordo/murielle_saade_collab
git clone https://github.com/andresgordoortiz/murielle_saade_CRG_2026.git \
  /users/aaljord/agordo/murielle_saade_collab/analysis_2026
cd /users/aaljord/agordo/murielle_saade_collab/analysis_2026
```

The analysis clone and `raw_data_2026` are sibling directories. The existing VAST workflow stays at `/users/aaljord/agordo/git/vast-tools_nextflow`; do not clone this analysis project over it. Pixi is only needed for optional diagnostic reproduction, not to submit either analysis pipeline on CRG.

Review [config/cluster.env](config/cluster.env). Defaults are:

| Purpose | Location |
|---|---|
| Raw FASTQs | `/users/aaljord/agordo/murielle_saade_collab/raw_data_2026` |
| Existing VAST workflow clone | `/users/aaljord/agordo/git/vast-tools_nextflow` |
| VASTDB parent | `/users/aaljord/agordo/VASTDB` |
| Genome/GTF downloads | `/users/aaljord/agordo/murielle_saade_collab/references/ensembl115_GRCh38` |
| Temporary work and container cache | `/nfs/scratch01/aaljord/agordo/murielle_saade_2026` |

The reference stage downloads approximately 1 GB of genome/GTF and the approximately 5 GB Hs2 archive if Hs2 is absent. Allow substantially more scratch space for cleaned reads, alignments, indexes and Nextflow work; availability was not checked on CRG. Keep work directories until results are verified so `-resume` can reuse successful tasks.

```bash
cd /users/aaljord/agordo/murielle_saade_collab/analysis_2026
bash scripts/submit.sh
```

The RNA-seq job verifies all 18 transferred SHA256s before processing. Sample sheets are regenerated against the cluster files and checked for missing/empty mates. No glob is used to infer replicate groups. `logs/` contains driver logs; each pipeline keeps its own Nextflow state in `runs/rnaseq` or `runs/vast`.

The driver requests 6 GB on `genoa64` with QOS `pipelines`, matching your local workflow wrapper. Tasks use Slurm with the wrapper's time-dependent QOS mapping, at most 16 CPUs / 128 GB / 7 days per task. The reference download job uses an 8-hour `normal` allocation. Modules are `Nextflow`, `Java` and `Singularity/4.0.2`; `NXF_VER=25.10.4` pins the Nextflow engine required by rnaseq 3.27.0. These site settings come from the local VAST clone; live module, QOS and account permissions were not queried.

If a stage fails, fix the reported issue and resubmit that stage, then submit its dependent stage after it succeeds:

```bash
sbatch --output=logs/rnaseq.%j.log scripts/run_pipeline.sbatch rnaseq "$PWD"
# Once rnaseq completes successfully:
sbatch --output=logs/vast.%j.log scripts/run_pipeline.sbatch vast "$PWD"
```

These commands reuse the separate pipeline caches through `-resume`. Cancel any old jobs still pending on a failed dependency before resubmitting the whole chain.

## Why these parameters

- **GRCh38 in both pipelines:** VAST's official hg38 library is Hs2. Its scaffold annotation is Ensembl 88; the DE annotation is Ensembl 115 on the same GRCh38 assembly. Annotation releases differ, so a gene or event absent from one catalogue is not evidence for biological absence. [VASTDB libraries](https://github.com/vastgroup/vast-tools#vastdb-libraries)
- **Paired-end:** matching read identifiers and `/1` versus `/2` suffixes establish sequencing mates. Each biological replicate remains separate.
- **Strandedness `auto`:** independently validate each sample in nf-core, while recording the observed strand inference in the QC report. VAST also infers strand internally. [nf-core usage](https://nf-co.re/rnaseq/3.27.0/docs/usage/), [VAST strandedness](https://github.com/vastgroup/vast-tools#strand-specific-rnaseq-data)
- **fastp:** paired overlap-based adapter trimming and automatic paired-end adapter detection handle the observed short-read format without assuming Illumina adapters. The reads' identifiers suggest MGI/DNBSEQ. Keep reads at least 35 nt long. The VAST run consumes nf-core's saved `fastp/*_R{1,2}.fastp.fastq.gz`, so trimming happens once.
- **No UMI processing:** no cell barcode/UMI structure was supplied; both mates are 150-base transcript reads. This is consistent with conventional bulk RNA-seq, but does not identify the library kit.
- **Keep standard alignment and RNA QC:** STAR junction-aware alignment, Salmon gene/transcript estimates, FastQC, RSeQC, Qualimap, duplication marking and DESeq2 sample QC. StringTie and bigWig generation are skipped because the requested products are count and inclusion tables. No downsampling, rRNA removal, or biological-replicate merging is requested.
- **Skip VAST compare/betAS/MATT:** the requested endpoint is the inclusion table. The inspected VAST workflow incorrectly connects paired-end sequencing to `vast-tools compare --paired`, which means matched biological replicates. Disabling comparisons avoids that error for these independent samples. Revisit the upstream comparison code before using it here.

The inspected VAST clone was at commit `866fe0f544489322b59d04bad0c258657acffa0b`. It is not modified or copied into this repo. Its containers include mutable `latest` tags; record the cluster clone revision and actual container identities when running the final analysis.

## Reproduce local inspection

All added software lives in this repository's locked Pixi environment:

```bash
pixi install --locked
pixi run bash scripts/run_local_qc.sh /home/andgortiz/Downloads/Murielle_Saade_API
pixi run python -m unittest discover -s tests
```

`run_local_qc.sh` verifies checksums, checks 100,000 paired records per sample, saves those subsets and produces subset fastp reports. Local execution is limited to one CPU, low CPU/IO priority and 3 GB virtual memory; it skips full-file seqkit scans. No further local scans were run after the overload. On Slurm, it also scans all 18 full FASTQs with seqkit. The nf-core cluster run independently performs full-read QC.

`screen_species.sh` compares the subsets competitively against Ensembl 115 human and mouse cDNA + ncRNA using minimap2. Its index peaked near 7 GB RAM, so the script now refuses local execution. If reproducing it on a cluster with Pixi available, request at least 12 GB RAM and 4 CPUs; run it after the subset files exist. The large diagnostic references, subsets and BAMs are ignored by Git.

Local validation cannot establish organoid identity, the knockout gene, batch/donor structure, library kit, RNA integrity, contamination outside the diagnostic reference set, or biological reproducibility. Review the full cluster MultiQC and sample PCA before interpreting DE or splicing changes.
