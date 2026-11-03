# Stable Experiment V results

Completed fresh full-size run: 12,720 metrics, 530 sketches, all support gates passed.
OPT has the lowest observed mean in 78/78 cells.

The old and new runs use different seeds and, for three methods, different numerical targets. Mean changes cannot be attributed solely to the step size.

| Data | Method | Rule | Old mean | New mean | New first-order ratio |
|---|---|---|---:|---:|---:|
| gdsc | HBF | OPT | 0.0180625551 | 0.0182312671 | 1.08166 |
| gdsc | HBF | UNI | 0.0281461038 | 0.0277358813 | 0.997458 |
| gdsc | Landweber | OPT | 0.0206293308 | 0.0204430391 | 1.07437 |
| gdsc | Landweber | UNI | 0.0327157148 | 0.032267824 | 1.01776 |
| gdsc | Nesterov | OPT | 0.0163316561 | 0.0161799258 | 1.05847 |
| gdsc | Nesterov | UNI | 0.0256946692 | 0.0250294768 | 0.993691 |
| gdsc | Ridge | OPT | 0.028699602 | 0.0285742488 | 1.17943 |
| gdsc | Ridge | UNI | 0.0446868595 | 0.0439732229 | 1.07923 |
| gdsc | SOAR | OPT | 0.0154558876 | 0.0162446565 | 1.06757 |
| gdsc | SOAR | UNI | 0.0252484804 | 0.0249030077 | 0.993414 |
| gdsc | Showalter | OPT | 0.0204748671 | 0.0204426369 | 1.07435 |
| gdsc | Showalter | UNI | 0.0327123783 | 0.0322675862 | 1.01777 |
| year | HBF | OPT | 0.00370335149 | 0.00364195538 | 0.998813 |
| year | HBF | UNI | 0.0103978935 | 0.0101278412 | 0.926894 |
| year | Landweber | OPT | 0.00295470542 | 0.00297731808 | 1.00396 |
| year | Landweber | UNI | 0.00890904912 | 0.00865348772 | 0.95485 |
| year | Nesterov | OPT | 0.00289386532 | 0.00288872627 | 0.969024 |
| year | Nesterov | UNI | 0.00890786855 | 0.0086616676 | 0.951914 |
| year | Ridge | OPT | 0.00294110765 | 0.00299619051 | 1.01033 |
| year | Ridge | UNI | 0.00890901217 | 0.00865345042 | 0.95485 |
| year | SOAR | OPT | 0.00293105258 | 0.00331404117 | 1.10736 |
| year | SOAR | UNI | 0.00891873964 | 0.00866620709 | 0.950219 |
| year | Showalter | OPT | 0.00295470542 | 0.00297731808 | 1.00396 |
| year | Showalter | UNI | 0.00890904912 | 0.00865348772 | 0.95485 |

Stability excludes the identified exponential numerical amplification. It does not by itself certify finite-budget full MSE ordering.

See independent_validation.json, support_gate.json, old_new_comparison.csv and target_changes.csv.
