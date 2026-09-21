"""
SE3062 Practical 06 - Genetic Algorithm for the 0/1 Knapsack problem (DEAP).

Runs the baseline and every one-factor-at-a-time comparison from the lab sheet,
writes CSV results and plots into ./results.

Usage (from the repository root):
    Practical_06\\.venv\\Scripts\\python Practical_06\\deap_ga.py

Sources / references:
  - DEAP toolbox pattern: https://deap.readthedocs.io/ (base, creator, tools)
  - Lab sheet scaffold (deap_ga.py) provided in SE3062 Practical 06.
  - Dataset: Pisinger hard 0/1 knapsack instances, see README.md.
"""
import argparse
import csv
import os
import random
import statistics

import matplotlib
matplotlib.use("Agg")                      # save figures, never open a window
import matplotlib.pyplot as plt
from deap import base, creator, tools

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "data", "knapPI_11_100_1000_50.csv")
RESULTS_DIR = os.path.join(HERE, "results")

SEEDS = [42, 43, 44, 45, 46]

BASELINE = dict(select="tournament", tourn_k=3, cx="2pt", pc=0.9, pm=0.02,
                elite=2, gens=200, pop_size=150)


# --------------------------------------------------------------------------
# Instance loading and fitness
# --------------------------------------------------------------------------
def load_instance(path=DATA_FILE):
    """Read and validate a Pisinger CSV instance. Returns (v, w, C)."""
    v, w = [], []
    capacity = n = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("knapPI"):
                continue
            if line.startswith("c "):
                capacity = int(line.split()[1])
            elif line.startswith("n "):
                n = int(line.split()[1])
            elif line[0].isdigit():                 # "id,profit,weight,x"
                item_id, p, wt, _ = line.split(",")
                if int(item_id) != len(v) + 1:
                    raise ValueError("Item IDs must be sequential, starting at 1")
                v.append(int(p))
                w.append(int(wt))
    if n is None or n < 2 or len(v) != n:
        raise ValueError("Item count does not match the n header (minimum 2)")
    if capacity is None or capacity <= 0 or any(x <= 0 for x in v + w):
        raise ValueError("Capacity, profits and weights must be positive")
    return v, w, capacity


def load_optimum(path=DATA_FILE):
    """Read the reference optimum, used only for reporting, never by the GA."""
    with open(path) as f:
        for line in f:
            if line.startswith("z "):
                optimum = int(line.split()[1])
                if optimum > 0:
                    return optimum
    raise ValueError("A positive z header is required for optimum comparisons")


def make_fitness(v, w, C, hard=True, M=1000):
    """Hard penalty: value - M * overweight (as in the lab sheet)."""
    def fitness(ind):
        val = sum(g * vi for g, vi in zip(ind, v))
        wt = sum(g * wi for g, wi in zip(ind, w))
        of = max(0, wt - C)
        return (val - M * of,) if hard else (val / (1 + of),)
    return fitness


def describe(ind, v, w, C):
    """Value, weight, feasibility and fitness of one chromosome."""
    value = sum(g * vi for g, vi in zip(ind, v))
    weight = sum(g * wi for g, wi in zip(ind, w))
    return dict(value=value, weight=weight, feasible=weight <= C,
                fitness=value - 10 * max(v) * max(0, weight - C))


# --------------------------------------------------------------------------
# Selection operators
# --------------------------------------------------------------------------
def sel_roulette(pop, n):
    """Fitness-proportional selection. Fitness can be negative (penalty), so it
    is shifted by the population minimum first."""
    fits = [ind.fitness.values[0] for ind in pop]
    low = min(fits)
    weights = [f - low + 1.0 for f in fits]
    return random.choices(pop, weights=weights, k=n)


def sel_rank(pop, n):
    """Linear rank selection: probability proportional to rank (1 = worst)."""
    ordered = sorted(pop, key=lambda ind: ind.fitness.values[0])
    weights = list(range(1, len(ordered) + 1))
    return random.choices(ordered, weights=weights, k=n)


# --------------------------------------------------------------------------
# Toolbox
# --------------------------------------------------------------------------
def build_toolbox(n, fitness_fn, cx="2pt", select="tournament", tourn_k=3, pm=0.02):
    # creator.create registers global classes; guard so repeated calls are safe.
    if not hasattr(creator, "FitnessMax"):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMax)

    tb = base.Toolbox()
    tb.register("attr_bool", random.randint, 0, 1)
    tb.register("individual", tools.initRepeat, creator.Individual, tb.attr_bool, n=n)
    tb.register("population", tools.initRepeat, list, tb.individual)
    tb.register("evaluate", fitness_fn)

    if cx == "1pt":
        tb.register("mate", tools.cxOnePoint)
    elif cx == "2pt":
        tb.register("mate", tools.cxTwoPoint)
    elif cx == "uniform":
        tb.register("mate", tools.cxUniform, indpb=0.5)
    else:
        raise ValueError(f"unknown crossover {cx}")

    tb.register("mutate", tools.mutFlipBit, indpb=pm)      # pm is per gene

    if select == "tournament":
        tb.register("select", tools.selTournament, tournsize=tourn_k)
    elif select == "roulette":
        tb.register("select", sel_roulette)
    elif select == "rank":
        tb.register("select", sel_rank)
    else:
        raise ValueError(f"unknown selection {select}")
    return tb


# --------------------------------------------------------------------------
# GA loop with explicit elitism
# --------------------------------------------------------------------------
def gene_diversity(pop):
    """Mean over genes of 2p(1-p): 0.5 = fully mixed, 0 = all identical."""
    n, size = len(pop[0]), len(pop)
    total = 0.0
    for j in range(n):
        p = sum(ind[j] for ind in pop) / size
        total += 2 * p * (1 - p)
    return total / n


def run(v, w, C, seed, gens=200, pop_size=150, pc=0.9, pm=0.02, elite=2, **ops):
    """One GA run. Returns (best_individual, history)."""
    random.seed(seed)
    fitness_fn = make_fitness(v, w, C, hard=True, M=10 * max(v))
    tb = build_toolbox(len(v), fitness_fn, pm=pm, **ops)

    pop = tb.population(n=pop_size)
    for ind in pop:
        ind.fitness.values = tb.evaluate(ind)

    hist = dict(best=[], avg=[], best_weight=[], best_feasible_value=[],
                diversity=[], infeasible_frac=[])
    hof = tools.HallOfFame(1)

    def log(population):
        fits = [ind.fitness.values[0] for ind in population]
        best = tools.selBest(population, 1)[0]
        infos = [describe(i, v, w, C) for i in population]
        feas = [d["value"] for d in infos if d["feasible"]]
        hist["best"].append(max(fits))
        hist["avg"].append(sum(fits) / len(fits))
        hist["best_weight"].append(describe(best, v, w, C)["weight"])
        hist["best_feasible_value"].append(max(feas) if feas else None)
        hist["diversity"].append(gene_diversity(population))
        hist["infeasible_frac"].append(1 - len(feas) / len(population))
        hof.update(population)

    log(pop)                                            # generation 0
    for _ in range(gens):
        elites = [tb.clone(i) for i in tools.selBest(pop, elite)]
        elite_snapshot = [(tuple(i), i.fitness.values) for i in elites]

        offspring = [tb.clone(i) for i in tb.select(pop, pop_size - elite)]
        for a, b in zip(offspring[::2], offspring[1::2]):
            if random.random() < pc:
                tb.mate(a, b)
                del a.fitness.values, b.fitness.values
        for ind in offspring:
            tb.mutate(ind)
            del ind.fitness.values
        for ind in offspring:
            if not ind.fitness.valid:
                ind.fitness.values = tb.evaluate(ind)

        pop = elites + offspring
        # Verify elitism: the E best of the previous generation survive unchanged.
        if [(tuple(i), i.fitness.values) for i in pop[:elite]] != elite_snapshot:
            raise RuntimeError("elitism violated")
        log(pop)
        if elite and hist["best"][-1] < hist["best"][-2]:
            raise RuntimeError("Best fitness decreased despite elitism")

    return hof[0], hist


# --------------------------------------------------------------------------
# Experiment definitions (one factor changed at a time)
# --------------------------------------------------------------------------
def variants():
    def change(**kw):
        d = dict(BASELINE)
        d.update(kw)
        return d
    return {
        "Baseline (k=3, 2pt, pm=0.02)": change(),
        # selection
        "Tournament k=2": change(tourn_k=2),
        "Tournament k=4": change(tourn_k=4),
        "Roulette": change(select="roulette"),
        "Rank": change(select="rank"),
        # crossover
        "1-point crossover": change(cx="1pt"),
        "Uniform crossover": change(cx="uniform"),
        # mutation
        "pm = 0.01": change(pm=0.01),
        "pm = 0.05": change(pm=0.05),
        "pm = 0.10": change(pm=0.10),
    }


GROUPS = {
    "selection": ["Baseline (k=3, 2pt, pm=0.02)", "Tournament k=2", "Tournament k=4",
                  "Roulette", "Rank"],
    "crossover": ["1-point crossover", "Baseline (k=3, 2pt, pm=0.02)", "Uniform crossover"],
    "mutation": ["pm = 0.01", "Baseline (k=3, 2pt, pm=0.02)", "pm = 0.05", "pm = 0.10"],
}
BASE_NAME = "Baseline (k=3, 2pt, pm=0.02)"


def first_generation_reaching(best_curve, target):
    """First generation whose best fitness is >= target, else None."""
    for g, val in enumerate(best_curve):
        if val >= target:
            return g
    return None


def run_all(v, w, C, seeds):
    results = {}                    # name -> list of dict(seed, best, hist)
    for name, cfg in variants().items():
        results[name] = []
        for seed in seeds:
            best, hist = run(v, w, C, seed, **cfg)
            info = describe(best, v, w, C)
            results[name].append(dict(seed=seed, best=best, info=info, hist=hist))
        print(f"done: {name}")
    return results


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def write_history(results):
    """Persist generation 0 through 200 for every variant and seed."""
    with open(os.path.join(RESULTS_DIR, "generation_history.csv"), "w", newline="") as f:
        keys = list(results[BASE_NAME][0]["hist"])
        writer = csv.DictWriter(f, fieldnames=["variant", "seed", "generation"] + keys)
        writer.writeheader()
        for name, runs in results.items():
            for r in runs:
                for g in range(len(r["hist"]["best"])):
                    writer.writerow(dict(variant=name, seed=r["seed"], generation=g,
                                         **{k: r["hist"][k][g] for k in keys}))


def write_csv_and_summary(results, C, optimum):
    base_finals = [r["info"]["fitness"] for r in results[BASE_NAME]]
    ref = statistics.median(base_finals)

    rows, summary = [], []
    for name, runs in results.items():
        gens_reached = []
        for r in runs:
            g = first_generation_reaching(r["hist"]["best"], ref)
            r["gen_to_ref"] = g
            gens_reached.append(g)
            rows.append(dict(variant=name, seed=r["seed"],
                             final_best_fitness=r["info"]["fitness"],
                             best_value=r["info"]["value"],
                             best_weight=r["info"]["weight"], capacity=C,
                             feasible=r["info"]["feasible"],
                             generation_to_baseline_median="Not reached" if g is None else g))
        finals = [r["info"]["fitness"] for r in runs]
        reached = [g for g in gens_reached if g is not None]
        # runs that never reach the reference count as infinity in the median
        med = statistics.median([g if g is not None else float("inf")
                                 for g in gens_reached])
        # Extra metric (not in the lab sheet): generations to reach 99% of the optimum.
        g99 = [first_generation_reaching(r["hist"]["best"], 0.99 * optimum) for r in runs]
        med99 = statistics.median([g if g is not None else float("inf") for g in g99])
        summary.append(dict(
            variant=name, mean=statistics.mean(finals), sd=statistics.stdev(finals),
            min=min(finals), max=max(finals),
            reached=f"{len(reached)}/{len(runs)}",
            median_gen="Not reached" if med == float("inf") else f"{med:g}",
            reached_99=f"{sum(g is not None for g in g99)}/{len(runs)}",
            median_gen_99="Not reached" if med99 == float("inf") else f"{med99:g}",
            final_diversity=statistics.mean(r["hist"]["diversity"][-1] for r in runs),
            final_infeasible=statistics.mean(r["hist"]["infeasible_frac"][-1] for r in runs),
            mean_avg_final=statistics.mean(r["hist"]["avg"][-1] for r in runs)))

    with open(os.path.join(RESULTS_DIR, "experiment_results.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    with open(os.path.join(RESULTS_DIR, "summary.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        wr.writeheader()
        wr.writerows(summary)

    lines = [f"Known optimum z = {optimum}, capacity C = {C}, seeds = {SEEDS}",
             f"Reference for convergence speed = median of baseline final best fitness = {ref:g}", ""]
    lines.append(f"{'Variant':32s} {'mean +- sd':>20s} {'min':>7s} {'max':>7s} "
                 f"{'reached':>8s} {'median gen':>11s} {'gen@99%':>9s} {'end diversity':>14s} {'end infeas.':>12s}")
    for s in summary:
        lines.append(f"{s['variant']:32s} {s['mean']:>10.1f} +- {s['sd']:<7.1f} "
                     f"{s['min']:>7d} {s['max']:>7d} {s['reached']:>8s} "
                     f"{s['median_gen']:>11s} {s['median_gen_99']:>9s} "
                     f"{s['final_diversity']:>14.4f} {s['final_infeasible']:>12.2f}")
    text = "\n".join(lines)
    with open(os.path.join(RESULTS_DIR, "summary.txt"), "w") as f:
        f.write(text + "\n")
    print("\n" + text)
    return ref


def mean_curve(runs, key):
    n = len(runs[0]["hist"][key])
    return [statistics.mean(r["hist"][key][g] for r in runs) for g in range(n)]


def plot_baseline(results, optimum):
    runs = results[BASE_NAME]
    best = mean_curve(runs, "best")
    avg = mean_curve(runs, "avg")
    lo = [min(r["hist"]["best"][g] for r in runs) for g in range(len(best))]
    hi = [max(r["hist"]["best"][g] for r in runs) for g in range(len(best))]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]                      # best and average, symmetric-log y axis
    ax.plot(best, label=f"best (mean of {len(runs)} seeds)")
    ax.plot(avg, label=f"average (mean of {len(runs)} seeds)")
    ax.axhline(optimum, color="gray", ls="--", lw=1, label=f"known optimum {optimum}")
    ax.set_yscale("symlog", linthresh=1e5)
    ax.set_title("Best and average fitness (symlog y-axis)")
    ax = axes[1]                      # zoom on best only
    ax.plot(best, label=f"best (mean of {len(runs)} seeds)")
    ax.fill_between(range(len(best)), lo, hi, alpha=0.2, label="best (min-max)")
    ax.axhline(optimum, color="gray", ls="--", lw=1, label=f"known optimum {optimum}")
    ax.set_ylim(optimum * 0.9, optimum * 1.005)
    ax.set_title("Best fitness, zoomed near the optimum")
    for ax in axes:
        ax.set_xlabel("Generation")
        ax.set_ylabel("Fitness")
        ax.legend(fontsize=8)
    fig.suptitle("Baseline GA convergence (k=3, 2-point, pc=0.9, pm=0.02, E=2)")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "baseline_convergence.png"), dpi=150)
    plt.close(fig)


def plot_group(results, group, optimum):
    names = GROUPS[group]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for name in names:
        runs = results[name]
        axes[0].plot(mean_curve(runs, "best"), label=name)
        axes[1].plot(mean_curve(runs, "avg"), label=name)
    axes[0].axhline(optimum, color="gray", ls="--", lw=1)
    axes[0].set_ylim(optimum * 0.85, optimum * 1.005)
    axes[0].set_title(f"Best fitness (mean of {len(runs)} seeds, zoomed)")
    axes[1].set_title(f"Average fitness (mean of {len(runs)} seeds, symlog y-axis)")
    axes[1].set_yscale("symlog", linthresh=1e5)
    for ax in axes:
        ax.set_xlabel("Generation")
        ax.set_ylabel("Fitness")
        ax.legend(fontsize=8)
    fig.suptitle(f"{group.capitalize()} comparison (all else at baseline)")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, f"{group}_comparison.png"), dpi=150)
    plt.close(fig)


def write_best_solution(results, v, w, C, optimum):
    best_run = max(results[BASE_NAME], key=lambda r: r["info"]["fitness"])
    ind, info = best_run["best"], best_run["info"]
    chosen = [i + 1 for i, g in enumerate(ind) if g]        # 1-based item ids
    text = (f"Baseline best run: seed {best_run['seed']}\n"
            f"Chromosome: {''.join(map(str, ind))}\n"
            f"Selected items (1-based ids): {chosen}\n"
            f"Number of items selected: {len(chosen)}\n"
            f"Total value: {info['value']}\nTotal weight: {info['weight']}\n"
            f"Capacity: {C}\nFeasible: {info['feasible']}\n"
            f"Fitness: {info['fitness']}\nKnown optimum: {optimum}\n")
    with open(os.path.join(RESULTS_DIR, "baseline_best_solution.txt"), "w") as f:
        f.write(text)
    print("\n" + text)


def main():
    global SEEDS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--data", default=DATA_FILE)
    parser.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    args = parser.parse_args()
    if len(set(args.seeds)) < 2 or len(set(args.seeds)) != len(args.seeds):
        parser.error("Provide at least two distinct seeds for sample standard deviation")
    SEEDS = args.seeds

    os.makedirs(RESULTS_DIR, exist_ok=True)
    v, w, C = load_instance(args.data)
    optimum = load_optimum(args.data)
    print(f"n = {len(v)}, C = {C}, known optimum = {optimum}, "
          f"M = {10 * max(v)}, seeds = {SEEDS}")

    results = run_all(v, w, C, SEEDS)
    write_history(results)
    write_csv_and_summary(results, C, optimum)
    write_best_solution(results, v, w, C, optimum)
    plot_baseline(results, optimum)
    for group in GROUPS:
        plot_group(results, group, optimum)
    print("Results written to", RESULTS_DIR)


if __name__ == "__main__":
    main()
