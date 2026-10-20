args <- commandArgs(TRUE)
stopifnot(length(args) == 2L,
          args[2] %in% c('WT_vs_KO3', 'WT_vs_KO25', 'KO3_vs_KO25'))
root <- normalizePath(args[1], mustWork = TRUE)
contrast <- args[2]
groups <- strsplit(contrast, '_vs_', fixed = TRUE)[[1]]
sha <- 'cd37737c75ab17a64652baf2fdb00d1b7c67c294'
stopifnot(as.character(getRversion()) == '4.5.2', requireNamespace('betAS', quietly = TRUE),
          identical(packageDescription('betAS')$RemoteSha, sha))
input <- file.path(root, 'results/vast/inclusion_tables/murielle_saade_2026_INCLUSION_LEVELS_FULL-hg38.tab')
metadata <- file.path(root, 'samples/metadata.tsv')
meta <- read.delim(metadata, stringsAsFactors = FALSE)
stopifnot(!anyDuplicated(meta$sample), nrow(meta) == 9L,
          setequal(meta$sample, unlist(lapply(c('WT', 'KO3', 'KO25'), function(g) paste0(g, '_', 1:3)))),
          all(meta$condition == sub('_[123]$', '', meta$sample)))
raw <- betAS::getDataset(input, tool = 'vast-tools')
annotation <- c('GENE', 'EVENT', 'COORD', 'LENGTH', 'FullCO', 'COMPLEX')
stopifnot(identical(names(raw)[1:6], annotation), !anyNA(raw$EVENT), !anyDuplicated(raw$EVENT),
          setequal(names(raw), c(annotation, meta$sample, paste0(meta$sample, '.Q'))))
meta <- meta[meta$condition %in% groups, ]
raw <- raw[, c(annotation, as.vector(rbind(meta$sample, paste0(meta$sample, '.Q'))))]
events <- betAS::getEvents(raw, tool = 'vast-tools')
filtered <- betAS::filterEvents(events, N = 10)
psi <- filtered$PSI; qual <- filtered$Qual
stopifnot(nrow(psi) > 0L, !anyNA(psi), identical(psi$EVENT, qual$EVENT),
          all(is.finite(as.matrix(psi[-(1:6)]))),
          all(as.matrix(psi[-(1:6)]) >= 0 & as.matrix(psi[-(1:6)]) <= 100))
coverage <- sapply(qual[-(1:6)], function(q) {
  counts <- strsplit(sub('.*@', '', q), ',', fixed = TRUE)
  stopifnot(all(lengths(counts) == 2L))
  counts <- matrix(as.numeric(unlist(counts)), ncol = 2L, byrow = TRUE)
  stopifnot(all(is.finite(counts)), all(counts >= 0))
  rowSums(counts)
})
stopifnot(all(coverage >= 10))
out <- file.path(root, 'results/betas', contrast)
identity <- list(input_md5 = unname(tools::md5sum(input)), metadata_md5 = unname(tools::md5sum(metadata)),
  script_md5 = unname(tools::md5sum(file.path(root, 'scripts/run_betas.R'))),
  contrast = contrast, betas_sha = sha, R = R.version.string,
  min_reads = 10L, npoints = 500L, nsim = 1000L, seed = 21122023L, coverage_weight = FALSE)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
atomic_rds <- function(x, path) {
  tmp <- paste0(path, '.', Sys.getpid(), '.tmp')
  saveRDS(x, tmp)
  if (!file.rename(tmp, path)) stop('Cannot save ', path)
}
run_file <- file.path(out, 'run.rds')
if (file.exists(run_file)) {
  if (!identical(readRDS(run_file), identity)) stop('Inputs/settings changed; move the old result directory: ', out)
} else {
  atomic_rds(identity, run_file)
}
if (file.exists(file.path(out, 'COMPLETE'))) unlink(file.path(out, 'COMPLETE'))
write.table(meta, file.path(out, 'samples.tsv'), sep = '\t', quote = FALSE, row.names = FALSE)
write.csv(as.data.frame(table(psi$COMPLEX)), file.path(out, 'retained_event_types.csv'), row.names = FALSE)
atomic_rds(filtered, file.path(out, 'filtered.rds'))
message(contrast, ': ', nrow(raw), ' input events; ', nrow(psi), ' pass N10 in all six samples')
reference <- new.env()
data('maxDevSimulationN100', package = 'betAS', envir = reference)
common <- list(psitable = psi, qualtable = qual, npoints = 500L,
  colsA = match(meta$sample[meta$condition == groups[1]], names(psi)),
  colsB = match(meta$sample[meta$condition == groups[2]], names(psi)),
  labA = groups[1], labB = groups[2], basalColor = '#777777', interestColor = '#CC3300',
  maxDevTable = reference$maxDevSimulationN100, seed = TRUE, CoverageWeight = FALSE)
stage <- function(name, calculate) {
  path <- file.path(out, paste0(name, '.rds'))
  if (file.exists(path)) {
    saved <- readRDS(path)
    stopifnot(identical(saved$identity, identity), identical(saved$results$EVENT, psi$EVENT))
    return(saved$results)
  }
  message('Starting ', name, ' on the entire filtered table')
  set.seed(21122023)
  result <- calculate()
  stopifnot(identical(result$EVENT, psi$EVENT))
  atomic_rds(list(identity = identity, results = result), path)
  invisible(gc())
  result
}
results <- stage('FDR', function() do.call(betAS::prepareTableVolcanoFDR, c(common, list(nsim = 1000L))))
for (name in c('Pdiff', 'Fstat')) {
  calculate <- if (name == 'Pdiff') betAS::prepareTableVolcano else betAS::prepareTableVolcanoFstat
  part <- stage(name, function() do.call(calculate, common))
  stopifnot(identical(part$EVENT, results$EVENT),
            isTRUE(all.equal(part$deltapsi, results$deltapsi, tolerance = 1e-12)))
  results[[name]] <- part[[name]]
}
stopifnot(all(is.finite(results$deltapsi)), all(is.finite(results$FDR)),
          all(results$FDR >= 0 & results$FDR <= 1), all(is.finite(results$Pdiff)),
          all(results$Pdiff >= 0 & results$Pdiff <= 1), !anyNA(results$Fstat))
write.csv(results, file.path(out, 'all_events.csv'), row.names = FALSE)
selected <- results$FDR <= 0.05 & abs(results$deltapsi) >= 0.10
write.csv(results[selected, ], file.path(out, 'differential.csv'), row.names = FALSE)
write.csv(results[selected & results$Pdiff >= 0.95, ], file.path(out, 'combination.csv'), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(out, 'sessionInfo.txt'))
writeLines('All statistics and CSV exports completed.', file.path(out, 'COMPLETE'))
