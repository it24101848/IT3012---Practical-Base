import random


def local_beam_search(initial_states, k, max_iters, objective_fn):
    """
    initial_states: list of k randomly generated starting positions
    k: the beam width (number of states to keep)
    objective_fn: the function we are trying to maximize
    """
    current_states = initial_states

    for iteration in range(max_iters):
        all_successors = []   # Will hold tuples of (state, fitness)

        # --- STEP 1, 2 & 3: Generate, Evaluate, and Pool Neighbors ---
        for state in current_states:
            # Generate 5 random neighbors for this specific state
            for _ in range(5):
                neighbor = state + random.uniform(-10, 10)   # generate
                fit = objective_fn(neighbor)                 # evaluate
                all_successors.append((neighbor, fit))       # pool

        # --- STEP 4: Prune the Beam (The Cut) ---
        all_successors.sort(key=lambda x: x[1], reverse=True)    # sort pool, best first
        current_states = [item[0] for item in all_successors[:k]]  # keep best k states

    return max(current_states, key=objective_fn)


# =====================================================================
# LOCAL TEST RUNNER - DO NOT MODIFY BELOW THIS LINE
# =====================================================================
if __name__ == "__main__":
    # Fix the random seed for reproducible testing
    random.seed(42)

    # NOTE: the lab PDF's runner is cut off after random.seed(42), so the lines
    # below are MY OWN local verification, not the instructor's hidden test.
    def parabola(x):
        return -(x - 25) ** 2          # maximum at x = 25

    k = 3
    starts = [random.uniform(-100, 100) for _ in range(k)]
    best = local_beam_search(starts, k, 50, parabola)
    print(f"Best state returned: {best:.4f} (fitness {parabola(best):.4f})")
    if abs(best - 25) < 1.0:
        print("SUCCESS: Local Beam Search found the peak of the parabola.")
    else:
        print("FAILED: best state is not close to the peak at x = 25.")
