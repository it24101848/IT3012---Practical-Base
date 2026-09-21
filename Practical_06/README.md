# SE3062 Practical 06 - Genetic Algorithms for 0/1 Knapsack

Student: IT24101848

Genetic algorithm (GA) solver for a standard 0/1 knapsack instance, plus a
one-factor-at-a-time comparison of selection, crossover and mutation settings.

- **Verified environment:** Python 3.13.5, DEAP 1.4.4, matplotlib 3.11.2
- **GA library:** DEAP only; matplotlib is used for plots
- **Code:** `deap_ga.py` (single file that runs every experiment)

## Dataset and source

`data/knapPI_11_100_1000_50.csv` is **instance 50 of `knapPI_11_100_1000.csv`**
from Pisinger's hard 0/1 knapsack instances, recorded in the existing project as extracted from the archive
`hardinstances_pisinger.tgz` at <https://hjemmesider.diku.dk/~pisinger/codes.html>
(D. Pisinger, University of Copenhagen).

Source verification: the author's index was accessible, but downloading the
archive timed out during this review. Exact agreement with the archive is
**NOT VERIFIED**. The existing dataset was preserved. Its header optimum was
independently confirmed by an exact dynamic-programming calculation.

| Item | Value |
|---|---|
| n (items) | 100 |
| C (capacity) | 17689 |
| Known optimal value z | 67165 (given in the file header) |
| File format | header lines `n`, `c`, `z`, then rows `id,profit,weight,x` |

A single-constraint Pisinger instance with 100 items was used, as explicitly
allowed by the lab sheet. `load_instance()` validates the item count, sequential
IDs and positive values, weights and capacity, then returns `(v, w, C)`.
`load_optimum()` separately reads the reference optimum; neither the optimum nor
the supplied solution bits are used to guide the GA.

## Installation (Windows PowerShell, from the repository root)

```powershell
python -m venv Practical_06\.venv
Practical_06\.venv\Scripts\Activate.ps1
python -m pip install deap==1.4.4 matplotlib==3.11.2
```

## Run

```powershell
python Practical_06\deap_ga.py
```

This takes roughly 3 minutes (10 variants x 5 seeds x 200 generations) and
prints a summary table. Optional flags: `--seeds 1 2 3` and `--data <file>`.
Use at least two distinct seeds. A custom dataset must use the same Pisinger
format, including a positive `z` header. Running the command regenerates the
results directory's experiment outputs. The report describes the default seeds.

## GA settings

| Component | Choice |
|---|---|
| Encoding | binary chromosome, length n = 100 (1 = item taken) |
| Fitness | hard penalty: `value - M * max(0, weight - C)`, `M = 10 * max(v)` = 18300 |
| Baseline selection | tournament, k = 3 |
| Baseline crossover | 2-point, pc = 0.9 |
| Baseline mutation | bit-flip, pm = 0.02 per gene |
| Elitism | E = 2 (explicit; the run raises an error if elites are lost) |
| Population / generations | 150 / 200 |
| Seeds | 42, 43, 44, 45, 46 (same seeds for every variant) |

Variants (one change at a time, everything else at baseline): tournament k = 2
and 4, roulette, rank; 1-point and uniform crossover; pm = 0.01, 0.05, 0.10.

Notes: pm is applied per gene to every offspring. DEAP has no rank selection and
its `selRoulette` cannot handle negative (penalised) fitness, so `sel_rank`
(linear rank) and `sel_roulette` (fitness shifted by the population minimum)
are small custom functions in `deap_ga.py`.

## Convergence-speed metric

Reference = median over the 5 baseline seeds of the final best fitness. For each
run, "generation to reach baseline median" is the first generation whose best
fitness is >= that reference; "Not reached" if it never happens. The summary
also gives an extra metric, generations to reach 99% of the known optimum.
Generation 0 is the initial population. Summary medians include unsuccessful
runs as infinity, displayed as "Not reached"; reach counts are reported alongside
them. Standard deviation is the sample SD (n-1 denominator). Here "reach" means
`>=`, not strict `>`: if the reference equals the optimum, exceeding it is impossible.

Diversity is the mean of `2*p*(1-p)` over genes, where `p` is the fraction of
individuals carrying a 1. It ranges from 0 (identical) to 0.5 (maximally mixed).
Population-average fitness includes penalised infeasible individuals. The plots
label their symlog axes and zoomed panels explicitly.

## Outputs (`Practical_06/results/`)

| File | Content |
|---|---|
| `experiment_results.csv` | per variant and seed: final best fitness, value, weight, capacity, feasible, generation to baseline median |
| `generation_history.csv` | all 10,050 generation records: variant, seed, generation, best/average fitness, best weight, best feasible value, diversity, infeasible fraction |
| `summary.csv`, `summary.txt` | mean, sd, min, max, reach counts, diversity, infeasible fraction |
| `baseline_best_solution.txt` | best baseline chromosome, selected items, value, weight |
| `baseline_convergence.png` | best/average fitness vs generation (baseline) |
| `selection_comparison.png`, `crossover_comparison.png`, `mutation_comparison.png` | comparison curves |

The optional harder-instance experiment was not performed.

## Report and validation

`REPORT.md` contains report-ready text based on the default 50 executed runs.
`results/validation.txt` records checks of the results and repository tests.

```powershell
python test_suite.py
python -m py_compile Practical_06\deap_ga.py
```

Implementation references: the supplied seven-page SE3062 Practical 06 lab
sheet and [DEAP tools documentation](https://deap.readthedocs.io/en/master/api/tools.html).
The explicit elitism loop replaces the scaffold's non-elitist `eaSimple` loop.
Review and acknowledge AI assistance according to your course's submission rules.
