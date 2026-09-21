# SE3062 – Intelligent Systems
## Practical 06: Genetic Algorithms for 0/1 Knapsack

**Student ID:** IT24101848

### A. Problem Summary

The 0/1 knapsack problem selects items to maximize total value without exceeding
a weight capacity. For item values v_i, weights w_i and capacity C, maximize
sum(v_i*x_i), subject to sum(w_i*x_i) <= C and x_i in {0,1}. A chromosome contains
one bit per item: 1 selects the item and 0 excludes it.

### B. Dataset

The existing dataset is `knapPI_11_100_1000_50.csv`, identified as instance 50 of
Pisinger's `knapPI_11_100_1000.csv` from `hardinstances_pisinger.tgz`.
It contains **100 items**, capacity **17,689**, and reference optimum **67,165**.
The source is [David Pisinger's knapsack instances](https://hjemmesider.diku.dk/~pisinger/codes.html),
an allowed collection in the lab sheet. The file contains n, c and z headers
and rows `id,profit,weight,x`. The loader returns `(v, w, C)`; reference solution
bits are ignored and the optimum is read separately for reporting only.
An independent exact dynamic-programming check confirmed the local optimum.
Exact agreement with the original archive is **NOT VERIFIED** because its
download timed out; the existing dataset was retained unchanged.

### C. GA Design

| Component | Baseline setting |
|---|---|
| Library | DEAP 1.4.4; Python 3.13.5 |
| Encoding | 100 binary genes |
| Fitness | value - 18,300 * max(0, weight - 17,689) |
| Selection | Tournament, k=3 |
| Crossover | 2-point, probability 0.9 per pair |
| Mutation | Bit-flip, probability 0.02 per gene on every offspring |
| Elitism | Two best individuals copied unchanged |
| Population / generations | 150 / 200 |
| Seeds | 42, 43, 44, 45, 46 for every variant |

The penalty multiplier is 10*max(v)=18,300. It strongly discourages overweight
solutions while allowing them to remain in the population. Feasible fitness
equals item value. Parents are cloned before variation, and unchanged elites
are copied into the next generation. Runtime checks verify elite preservation
and nondecreasing best fitness. Fitness, feasibility and diversity are recorded
from generation 0 through 200. Shifted roulette uses weights f-min(f)+1 to handle
negative fitness; rank selection uses weights 1 to 150 from worst to best.
These are custom selection functions within the DEAP implementation.

### D. Baseline Results

All five baseline runs found **67,165**, giving final best fitness
**67,165.0 ± 0.0** (mean ± sample SD). The representative seed-42 solution
selects 72 items with total weight **17,685**, capacity **17,689**, and fitness
**67,165**. It is feasible and equals the verified local optimum.

Chromosome (item 1 is the leftmost bit):

```text
1101111111111111111101110111001110011101010110110101111111011101111111001110011011110101111101000100
```

Selected item IDs (1-based):
1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
22, 23, 24, 26, 27, 28, 31, 32, 33, 36, 37, 38, 40, 42, 44, 45, 47, 48,
50, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 64, 65, 66, 67, 68, 69, 70,
73, 74, 75, 78, 79, 81, 82, 83, 84, 86, 88, 89, 90, 91, 92, 94, 98.

### E. Operator/Parameter Comparison

Each row changes only its named factor from the baseline. The reference is
the median final baseline fitness, **67,165**. A run's reach generation is the
first generation with best fitness >= reference. Summary medians include
unsuccessful runs as infinity, displayed as NR (not reached); success counts
are shown to avoid hiding failures. Equality is included because this reference
is already optimal. SD uses the n-1 denominator.

| Variant | Final best fitness, mean ± SD | Median reach generation (runs reached) |
|---|---:|---:|
| Baseline | 67,165.0 ± 0.0 | 75 (5/5) |
| Tournament k=2 | 66,885.2 ± 311.6 | NR (2/5) |
| Tournament k=4 | 67,165.0 ± 0.0 | 58 (5/5) |
| Shifted roulette | 62,546.2 ± 1,304.4 | NR (0/5) |
| Rank | 67,055.2 ± 100.2 | NR (2/5) |
| 1-point crossover | 67,128.4 ± 81.8 | 99 (4/5) |
| Uniform crossover | 67,128.4 ± 81.8 | 132 (4/5) |
| pm=0.01 | 67,165.0 ± 0.0 | 43 (5/5) |
| pm=0.05 | 65,808.4 ± 368.3 | NR (0/5) |
| pm=0.10 | 63,181.4 ± 1,113.7 | NR (0/5) |

### F. Convergence Analysis

Baseline mean best fitness rose from 50,561.8 at generation 0 to 65,892.2 at
generation 25 and 66,775.4 at generation 50. Seeds 42–46 first reached the
optimum at generations 57, 135, 96, 75 and 57 respectively. All best curves
then remained optimal. Thus identical final fitness does not imply identical
convergence speed. At generation 200, population-average fitness was
-2,532,162.46 across seeds, with 21.87% of individuals infeasible. Large
penalties explain the negative average despite optimal elites. Population
averages continued fluctuating; the whole population did not become optimal.

**Figure 1:** Insert `results/baseline_convergence.png`: mean best and population
average fitness with a labelled symlog axis, plus a zoomed best-fitness panel
whose shaded band shows the minimum–maximum over seeds, not a confidence interval.

**Figure 2:** Insert `results/mutation_comparison.png`: best and average fitness
for the four mutation rates. The selection and crossover plots are useful
supporting figures if space permits. Zoomed best panels omit early low values.

### G. Discussion

**Selection pressure and diversity.** Tournament k=4 reached the reference
earlier than k=3 (58 versus 75 median generations), while k=2 reached it in
only two runs. Final diversity, measured by mean 2p(1-p) over genes, was
0.1654, 0.1936 and 0.2597 for k=4, k=3 and k=2 respectively. Stronger pressure
therefore coincided with faster convergence and reduced diversity here, but
there is no evidence of harmful premature convergence for k=4: every run
reached the optimum. Rank retained diversity 0.2602 but reached the optimum
in two runs. Shifted roulette had diversity 0.4394 and the lowest final mean;
large negative outliers can make shifted positive weights similar, weakening
selection pressure. This mechanism is a plausible explanation, not a measured
causal result.

**Crossover.** Two-point crossover reached the optimum in all runs, compared
with four of five for both alternatives. One-point and uniform had equal
final means but median reach generations of 99 and 132. Uniform retained
greater final diversity (0.2208 versus 0.1824 for one-point). The results favor
two-point on this instance; the small sample does not establish universal superiority.

**Mutation.** pm=0.01 reached the optimum fastest and ended with diversity
0.0781. Increasing mutation to 0.05 and 0.10 raised diversity to 0.3520 and
0.4447 but reduced mean best fitness to 65,808.4 and 63,181.4. These results
are consistent with frequent flips disrupting useful combinations. Exploration
alone did not improve results within the fixed generation budget.

**Reproducibility.** All ten variants used the same five seeds and initial
sampling method, with only one setting changed at a time. The 50 final results
and 10,050 generation records are saved in CSV. Comparisons are descriptive,
limited to one instance and five seeds, without significance claims.

### H. Conclusion

The DEAP baseline consistently found an optimal feasible solution for the
local instance. Lower mutation and stronger tournament selection improved
median time to the optimum in separate experiments, while high mutation and
shifted roulette performed worse. Elitism preserved solution quality even
when population-average fitness remained negative. Optional harder-instance
experiment was not performed.

**Implementation references:** SE3062 Practical 06 lab sheet, all seven pages;
[DEAP tools](https://deap.readthedocs.io/en/master/api/tools.html); and the
Pisinger source cited above. The supplied scaffold informed the fitness and
toolbox structure; the explicit elitism loop and reporting extend it.
