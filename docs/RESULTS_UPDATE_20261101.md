# Results update: November 1, 2026

This update supplies the experimental results reported in the manuscript:

- Full-support stable Experiment V: 12,720 complete records, 530 paired sketch tasks and 48 passing support checks. OPT has the lowest observed mean in 78/78 cells among UNI/NORM/LEV/OPT; this is a finite-repetition comparison, not a complete conditional-MSE ordering.
- Simulated Ridge score comparison: 104,000 records on 40 existing inputs. At the sole primary budget N=150, FULL_OPT minus LN_floor is -0.0003228063, with 95% CI [-0.0009423789, 0.0002967663] and two-sided p=.298436. No significant difference was detected; equivalence is not established.
- GDSC Ridge Li-Niu comparison: 180 new LN_floor records and 720 preserved baseline records. The largest-budget OPT mean is 0.768% lower, with reversals at N=374/749 and all six pointwise paired intervals including zero.

The versioned implementations, full scalar metrics, protocols, source hashes, original validation receipts, six manuscript figure assets and saved-record analysis tools are included. Historical scientific sources, simulation inputs and the I-IV review-data descriptor are unchanged. The earlier v2026.10.30.2 release remains the separate archive for I-IV review data; the updated evidence is bundled in the current repository.

See [reported results](LATEST_RESULTS.md), [Chinese results](LATEST_RESULTS_CN.md), and the [figure/table map](PAPER_RESULTS.md) for commands, exact sources and statistical scope. No experiment is rerun as part of preparing this update.
