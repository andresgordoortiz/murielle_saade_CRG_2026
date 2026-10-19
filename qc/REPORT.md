# Raw-read inspection — 18 October 2026

**Conclusion:** all nine samples are consistent with **human, reverse-stranded, paired-end 150-base bulk RNA-seq**. The two FASTQs in each sample are sequencing mates, not technical replicates. The sampled base quality is good. Use **hg38 / GRCh38** in both analyses: VASTDB **Hs2** and the GRCh38 genome/GTF for gene counts.

**Resource incident and incomplete check:** parallel local QC saturated the CPU and the user reported that the PC crashed. Further heavy local processing was stopped. Five complete FASTQ scans were saved; thirteen are unfinished. No analysis processes were running when checked afterward. The local QC script is now limited to one CPU, low CPU/IO priority and 3 GB virtual memory, with full-file scans disabled locally. The large species screen now requires Slurm. Complete raw-read QC is delegated to the prepared nf-core cluster run.

## What was checked

- Inventory: **18 compressed FASTQs**, nine sample pairs, **51,699,434,353 bytes** total (about 48.2 GiB), under `Downloads/Murielle_Saade_API`.
- All **18 SHA256s match the supplied local `SHA256SUMS.flat` manifest**. The verified manifest is saved as `SHA256SUMS.cluster`; its filenames were flattened on 19 October to match the uploaded cluster layout. This verifies consistency with that manifest, not independent provider authenticity.
- The **first 100,000 pairs per sample** were read, validated and compared by cluster ID: **900,000 matching pairs**, with `/1` and `/2` suffixes and 150 bases in both mates. Mate order was not compared across the entire datasets.
- fastp inspected those 100,000 pairs per sample, with paired adapter detection and overlap-based trimming evaluated in reports only. **No raw files were modified and no trimmed reads were written locally.**
- Species screening aligned the same subsets competitively to Ensembl 115 human GRCh38 and mouse GRCm39 cDNA + ncRNA, using minimap2 short-read mode. Human assignments dominate every sample. Mouse is only a diagnostic comparator; its assembly is not an analysis reference.
- Strand inference used primary alignments with MAPQ >=20, at least 100 aligned query bases and at most seven mismatches/indels (NM). **96.72–97.93% of confidently mapped human R1 reads are reverse-oriented**, while R2 is predominantly forward. This is a reverse-stranded / first-strand library. nf-core is configured with `auto` to recheck each sample; VAST infers strand internally.
- seqkit completed scans of five FASTQs. The original partial results are retained as `seqkit_stats.partial.tsv`; the filename deliberately does not imply all files passed.

## Per-sample results

Q30, human alignment, strand and insert metrics below are from the **100,000-pair subsets**, not whole libraries. Human alignment percentages count primary mate alignments against the diagnostic transcriptomes. Strand percentages use the stricter confident-human subset; MAPQ filtering discards many reads shared between transcript isoforms.

| Sample | Full read-pair count | Sampled bases >=Q30 | Human primary alignment | Confident R1 reverse | Insert peak, bases |
|---|---:|---:|---:|---:|---:|
| WT_1 | not fully counted | 91.23% | 96.98% | 96.95% | 243 |
| WT_2 | not fully counted | 90.97% | 97.64% | 97.40% | 257 |
| WT_3 | not fully counted | 91.11% | 97.80% | 97.93% | 241 |
| KO3_1 | not fully counted | 90.96% | 97.23% | 97.79% | 246 |
| KO3_2 | not fully counted | 91.06% | 97.54% | 97.61% | 261 |
| KO3_3 | not fully counted | 91.53% | 97.94% | 97.61% | 246 |
| KO25_1 | 21,133,781 | 90.91% | 96.02% | 96.72% | 264 |
| KO25_2 | 22,097,628 | 91.56% | 96.99% | 97.31% | 243 |
| KO25_3 | not fully counted | 91.21% | 97.06% | 97.54% | 241 |

For KO25_3, R1 alone was fully counted: **21,470,198 reads**. Its R2 full scan is unfinished, so a full pair count is not claimed. Full-file Q30 percentages in the five completed scans were **91–94%**; all reads in those files were 150 bases long.

Across all nine subsets, **0.68–1.30% of mate reads** had adapter sequence trimmed in the fastp diagnostic, and all sampled pairs passed the default fastp read filters. Insert peaks were **241–264 bases**, supporting the paired-fragment interpretation. Sampled duplication estimates are not reliable whole-library complexity estimates and are not used to justify deduplication.

The two fully counted libraries have about **21–22 million pairs**, or 42–44 million individual mate reads. This is useful bulk RNA-seq depth, but splicing power will depend on informative junction coverage, gene expression and biological variability. Do not equate the supervisor's low-quality description with poor base quality; the measured limitation may be depth or sample biology. Coverage confidence in the VAST inclusion table must be reviewed before testing splicing changes.

## Assay and platform limits

The supervisor identifies these as bulk neural-tube organoid samples. Both mates contain long transcript-aligning sequences, consistent with conventional bulk RNA-seq rather than a standard short cell-barcode read paired with a transcript read. FASTQ content does not identify the exact library kit, poly(A) selection versus rRNA depletion, RNA integrity, donor/batch structure, or the knockout gene. Gene-body coverage, rRNA content and sample PCA need review after cluster alignment.

Identifiers such as `@E250124336L1C001R00300000054/1` resemble **MGI/DNBSEQ**, rather than the usual Illumina identifier layout. This is an inference, not a verified instrument model. MGI documents the lane/column/row/read identifier structure in its [sequencer system guide](https://global-mgitech.com/wp-content/uploads/Documents/H-020-001104-00-DNBSEQ-T1RSDNBSEQ-T1ARS-Genetic-Sequencer-System-Guide_English_RUO_SZ-2.pdf). The scripts use platform-independent short-read tools and paired-end adapter detection.

The human/mouse transcriptome screen is not an exhaustive contamination assay. The small mouse-assigned fraction can include conserved cross-species sequence and does not by itself establish contamination.

## Analysis references and parameters

Both analysis launches specify **GRCh38 / hg38**, which exists in [VASTDB as Hs2](https://github.com/vastgroup/vast-tools#vastdb-libraries). The reference preparation script downloads `vastdb.hs2.23.06.20.tar.gz` if Hs2 is absent, plus `Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz` and `Homo_sapiens.GRCh38.115.gtf.gz` from Ensembl 115. VAST's scaffold annotation is Ensembl 88 on GRCh38; the assembly matches even though the annotation release differs.

nf-core/rnaseq **3.27.0** runs STAR + Salmon with fastp and saves trimmed paired reads; VAST consumes exactly those saved reads with trimming disabled. Samples remain separate. Replicates are treated as independent, as instructed by the user. The VAST workflow's comparison stages are disabled because its paired-end flag is incorrectly connected to matched-sample statistical comparisons. Statistical DE tests are outside these count-table launch scripts.

## Validation and artifacts

- Five Python unit tests passed: FASTQ parsing/pair suffixes, species/strand counting, sample-sheet validation, and mocked Slurm dependencies including project paths with spaces.
- Bash syntax checks passed for every shell/submission script.
- Both resolved Nextflow configurations parsed with **Nextflow 25.10.4** and resolved to Slurm, `genoa64`, Singularity and the intended task resource limits.
- Both workflows completed **Nextflow preview runs**. VAST preview used the nine actual raw-file paths and an empty validation-only database directory; nf-core preview used those paths and a tiny synthetic reference. **No alignment, container execution or Slurm submission was performed by these previews.**
- Local tools: Python 3.12 from Pixi for reproducibility; fastp **0.24.3**, seqkit **2.14.0**, minimap2 **2.31-r1302**, and Nextflow **25.10.4**. Software was installed only in this repo's Pixi environment.
- VAST source inspected: `/home/andgortiz/Projects/vast-tools_nextflow`, commit `866fe0f544489322b59d04bad0c258657acffa0b`.

Evidence files: `pairing.json`, `inventory.tsv`, `SHA256SUMS.cluster`, `species_screen.tsv`, `seqkit_stats.partial.tsv`, and `fastp/*.json` / `*.html`. Nextflow preview and configuration logs are also retained. Large diagnostic reads, references and BAMs are ignored by Git.

Not checked: live CRG access, free space, module/QOS permissions, container execution, all-file read counts/CRC scans, final alignment metrics, inclusion-table coverage or DE results. The scripts are prepared for submission; they have not been submitted to CRG.

## Deployment update — 19 October 2026

The cluster raw files are flat under `/users/aaljord/agordo/murielle_saade_CRG_2026/raw_data_2026`. The committed nf-core and VAST sample sheets and checksum manifest now use that layout. Final outputs stay in `results/rnaseq` and `results/vast` inside the checkout; work directories are below `/nfs/scratch01/aaljord/agordo/murielle_saade_CRG_2026/`.

A further source review found mouse-only `ENSMUSG` junction filters in the shared VAST workflow. The launcher now makes a working copy with filters that retain human `ENSG` records and handle empty junction files without masking genuine grep errors. The original clone remains unchanged. These fixes were not exercised by the earlier preview. See the current README and tests for deployment validation; no heavy raw-read scans were repeated locally.
