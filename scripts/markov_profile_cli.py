#!/usr/bin/env python3
"""
Markov Operational Profile CLI

Given a Markov transition matrix for software modules,
compute the stationary distribution (operational profile)
and suggest a testing order (most frequently used modules first).

Example based on the A-B-C diagram:

Modules: A, B, C
Transition probabilities P[i -> j] in the order (A, B, C):

  From A: 0.5  0.5  0.0
  From B: 0.0  0.3  0.7
  From C: 0.4  0.0  0.6

This means:
- From A: 50% stay in A, 50% go to B
- From B: 30% stay in B, 70% go to C
- From C: 40% go to A, 60% stay in C

The script will compute π = [π_A, π_B, π_C] such that:
    π P = π   and   π_A + π_B + π_C = 1
"""

import numpy as np
from tabulate import tabulate


def get_int(prompt: str) -> int:
    """Prompt until the user enters a valid positive integer."""
    while True:
        s = input(prompt).strip()
        try:
            value = int(s)
            if value <= 0:
                print("Please enter a positive integer.")
            else:
                return value
        except ValueError:
            print("Please enter a valid integer.")


def get_float_row(prompt: str, n: int):
    """Prompt for a row of n floats (space- or comma-separated)."""
    while True:
        s = input(prompt).strip()
        # Allow both space and comma separators
        s = s.replace(",", " ")
        parts = [p for p in s.split() if p]

        if len(parts) != n:
            print(f"Please enter exactly {n} numbers.")
            continue

        try:
            row = [float(x) for x in parts]
        except ValueError:
            print("All entries must be numeric.")
            continue

        # Check probabilities are non-negative and row sums to ~1
        if any(p < 0 for p in row):
            print("Probabilities must be non-negative.")
            continue

        row_sum = sum(row)
        if not np.isclose(row_sum, 1.0, atol=1e-6):
            print(f"Row must sum to 1 (currently {row_sum:.6f}). "
                  "Please re-enter.")
            continue

        return row


def stationary_distribution(P: np.ndarray):
    """
    Solve for stationary distribution π such that:

        π P = π,   sum(π) = 1

    We solve the linear system:
        (P^T - I) π^T = 0
        sum(π) = 1
    """
    P = np.asarray(P, dtype=float)
    n = P.shape[0]

    # Build system A x = b
    A = P.T - np.eye(n)
    # Replace last equation with sum(π_i) = 1
    A[-1, :] = np.ones(n)

    b = np.zeros(n)
    b[-1] = 1.0

    pi = np.linalg.solve(A, b)

    # Numerical cleanup: clip small negatives and renormalize
    pi = np.maximum(pi, 0.0)
    pi = pi / pi.sum()

    return pi


def main():
    print("=== Markov Operational Profile & Test Priority CLI ===\n")

    print("You will provide:")
    print("  1) Number of modules (states).")
    print("  2) A name for each module.")
    print("  3) The transition probabilities P[i -> j] for each module i,\n"
          "     in the order of the module list you give.\n")

    print("Example (from A-B-C diagram):")
    print("  Modules: A, B, C")
    print("  Row for A (to A, B, C): 0.5 0.5 0.0")
    print("  Row for B (to A, B, C): 0.0 0.3 0.7")
    print("  Row for C (to A, B, C): 0.4 0.0 0.6\n")

    # 1. Number of modules
    n = get_int("Enter number of modules (states): ")

    # 2. Module names
    modules = []
    print()
    for i in range(n):
        name = input(f"Name for module {i + 1}: ").strip()
        if not name:
            name = f"M{i + 1}"
        modules.append(name)

    print("\nNow enter the transition probabilities.")
    print("For each module i, enter a row of probabilities P[i -> j]")
    print(f"in the order: {', '.join(modules)}")
    print("Each row must sum to 1.\n")

    # 3. Transition matrix
    P = []
    for i, src in enumerate(modules):
        row = get_float_row(
            f"Probabilities FROM {src} TO ({', '.join(modules)})(comma or space sep, no brackets): ",
            n
        )
        P.append(row)

    P = np.array(P, dtype=float)

    # Show the transition matrix
    print("\nTransition matrix P (rows = FROM, columns = TO):")
    header = ["FROM \\ TO"] + modules
    table_rows = []
    for i, src in enumerate(modules):
        table_rows.append([src] + [f"{p:.4f}" for p in P[i]])
    print(tabulate(table_rows, headers=header, tablefmt="grid"))

    # 4. Compute stationary distribution
    print("\nComputing stationary distribution (operational profile)...")
    pi = stationary_distribution(P)

    # 5. Show operational profile & testing priority
    print("\nOperational profile (long-run probability of being in each module):")
    prof_rows = []
    for m, p in zip(modules, pi):
        prof_rows.append([m, f"{p:.6f}", f"{100*p:6.2f}%"])

    print(tabulate(prof_rows,
                   headers=["Module", "π (probability)", "Usage %"],
                   tablefmt="grid"))

    # Sorted priority
    ranked = sorted(zip(modules, pi), key=lambda x: x[1], reverse=True)

    print("\nSuggested testing priority (most-used modules first):")
    rank_rows = []
    for idx, (m, p) in enumerate(ranked, start=1):
        rank_rows.append([idx, m, f"{p:.6f}", f"{100*p:6.2f}%"])

    print(tabulate(rank_rows,
                   headers=["Rank", "Module", "π (probability)", "Usage %"],
                   tablefmt="grid"))

    print("\nInterpretation:")
    print("  - π gives the long-run fraction of time spent in each module.")
    print("  - Higher π => module is exercised more often in operation,")
    print("    so it should generally receive more testing effort.\n")


if __name__ == "__main__":
    main()
