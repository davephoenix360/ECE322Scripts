#!/usr/bin/env python3
import itertools
import numpy as np
from tabulate import tabulate


# ------------------ Helpers ------------------


def get_int(prompt: str, min_value=None, max_value=None) -> int:
    while True:
        s = input(prompt).strip()
        try:
            x = int(s)
        except ValueError:
            print("  Please enter an integer.")
            continue
        if min_value is not None and x < min_value:
            print(f"  Must be >= {min_value}.")
            continue
        if max_value is not None and x > max_value:
            print(f"  Must be <= {max_value}.")
            continue
        return x


def get_float(prompt: str, min_value=None, max_value=None, default: float = None) -> float:
    while True:
        s = input(prompt).strip()
        if default is not None and s == "":
            return default
        try:
            x = float(s)
        except ValueError:
            print("  Please enter a number.")
            continue
        if min_value is not None and x < min_value:
            print(f"  Must be >= {min_value}.")
            continue
        if max_value is not None and x > max_value:
            print(f"  Must be <= {max_value}.")
            continue
        return x


def parse_vector(s: str, dim: int) -> np.ndarray:
    """
    Parse a vector from a string of comma/space-separated numbers.
    """
    s = s.replace(",", " ")
    parts = [p for p in s.split() if p]
    if len(parts) != dim:
        raise ValueError(f"Expected {dim} numbers, got {len(parts)}.")
    return np.array([float(x) for x in parts], dtype=float)


def matrix_rank(A: np.ndarray, tol: float) -> int:
    """
    Rank via SVD with a user-controlled tolerance.
    """
    if A.size == 0:
        return 0
    u, s, vt = np.linalg.svd(A, full_matrices=False)
    return int(np.sum(s > tol))


def read_real_vectors() -> np.ndarray:
    """
    Read k vectors in R^d from the user and return them as a matrix
    where vectors are rows: shape (k, d).
    """
    d = get_int("Enter vector dimension d (e.g., 4 for R^4): ", min_value=1)
    k = get_int("Enter number of vectors k: ", min_value=1)

    print("\nEnter each vector as d numbers, comma- or space-separated.")
    print("Example: 1, 0, 2, -3\n")

    rows = []
    for i in range(k):
        while True:
            raw = input(f"v{i+1}: ").strip()
            try:
                v = parse_vector(raw, d)
                rows.append(v)
                break
            except Exception as e:
                print(f"  {e} Try again.")

    return np.vstack(rows)


# ------------------ Mode 1: Linear Independence ------------------


def mode_linear_independence():
    print("\n=== Mode 1: Linear Independence Checker ===")
    V = read_real_vectors()  # rows are vectors

    tol = get_float("\nEnter tolerance for rank test (typical: 1e-10): ", min_value=0.0, default=1e-10)
    r = matrix_rank(V, tol=tol)
    k, d = V.shape

    indep = r == k
    max_indep = min(k, d)

    print("\nResults:")
    print(f"  Dimension d = {d}")
    print(f"  Number of vectors k = {k}")
    print(f"  Rank = {r}")
    print(f"  Max possible independent vectors here = min(k, d) = {max_indep}")
    print(f"  Linearly independent? {'YES' if indep else 'NO'}")

    if not indep:
        print(
            "  Interpretation: some vectors are redundant (can be written as a linear combo)."
        )
    else:
        print(
            "  Interpretation: vectors span k independent directions (good for weak n×1 with linear boundaries)."
        )
    print()


# ------------------ Fault Coverage / Set Cover ------------------


def parse_binary_vector(s: str, m: int) -> np.ndarray:
    """
    Parse a binary vector (0/1) length m from user input.
    Accepts: 1 0 1 1 or 1011 or 1,0,1,1
    """
    s = s.strip().replace(",", " ").replace("\t", " ")
    if all(ch in "01" for ch in s.replace(" ", "")) and len(s.replace(" ", "")) == m:
        bits = [int(ch) for ch in s.replace(" ", "")]
        return np.array(bits, dtype=int)

    parts = [p for p in s.split() if p]
    if len(parts) != m:
        raise ValueError(f"Expected {m} bits, got {len(parts)}.")
    bits = [int(x) for x in parts]
    if any(b not in (0, 1) for b in bits):
        raise ValueError("Bits must be 0 or 1.")
    return np.array(bits, dtype=int)


def read_fault_coverage() -> tuple[list[str], np.ndarray]:
    """
    Read test names and their fault-coverage vectors.
    Returns (names, M) where M has shape (t, m).
    """
    m = get_int("Enter number of faults (vector length m): ", min_value=1)
    t = get_int("Enter number of tests (number of vectors): ", min_value=1)

    names = []
    rows = []

    print("\nEnter each test's coverage vector (0/1) of length m.")
    print("Formats accepted: 1 0 1 1  OR  1011  OR  1,0,1,1\n")

    for i in range(t):
        name = input(f"Name for test {i+1} (default T{i+1}): ").strip() or f"T{i+1}"
        names.append(name)

        while True:
            raw = input(f"Coverage for {name}: ").strip()
            try:
                v = parse_binary_vector(raw, m)
                rows.append(v)
                break
            except Exception as e:
                print(f"  {e} Try again.")

    M = np.vstack(rows)
    return names, M


def exact_min_set_cover(M: np.ndarray):
    """
    Exact minimum set cover for small t (brute force).
    Returns indices of selected tests or None if impossible.
    """
    t, m = M.shape
    target = np.ones(m, dtype=int)

    for r in range(1, t + 1):
        for combo in itertools.combinations(range(t), r):
            covered = np.zeros(m, dtype=int)
            for idx in combo:
                covered |= M[idx]
            if np.array_equal(covered, target):
                return list(combo)
    return None


def greedy_set_cover(M: np.ndarray):
    """
    Greedy approximation: repeatedly pick test that covers most uncovered faults.
    Returns indices of selected tests or None if impossible.
    """
    t, m = M.shape
    uncovered = set(range(m))
    chosen = []

    while uncovered:
        best = None
        best_gain = 0

        for i in range(t):
            gain = sum(1 for f in uncovered if M[i, f] == 1)
            if gain > best_gain:
                best_gain = gain
                best = i

        if best is None or best_gain == 0:
            return None  # cannot cover remaining faults

        chosen.append(best)
        newly = {f for f in uncovered if M[best, f] == 1}
        uncovered -= newly

    return chosen


def mode_min_tests_cover_faults():
    print("\n=== Mode 2: Minimum Tests to Cover All Faults (Set Cover) ===")
    names, M = read_fault_coverage()
    t, m = M.shape

    print("\nCoverage matrix (rows=tests, cols=faults):")
    headers = ["Test"] + [f"F{j+1}" for j in range(m)]
    table = [[names[i]] + list(M[i]) for i in range(t)]
    print(tabulate(table, headers=headers, tablefmt="grid"))

    # Decide exact vs greedy
    # Brute force can explode; a common safe threshold is t <= 20-ish (still might be heavy).
    threshold = get_int("\nMax tests for exact search (suggest 20): ", min_value=1)

    if t <= threshold:
        print("\nRunning EXACT minimum set cover search...")
        chosen = exact_min_set_cover(M)
        method = "EXACT"
    else:
        print("\nToo many tests for exact search. Running GREEDY approximation...")
        chosen = greedy_set_cover(M)
        method = "GREEDY"

    if chosen is None:
        print(
            "\nNo subset of tests can cover all faults (some fault column is never hit).\n"
        )
        return

    chosen_names = [names[i] for i in chosen]
    covered = np.zeros(m, dtype=int)
    for i in chosen:
        covered |= M[i]

    print(f"\nSelected tests ({method}): {', '.join(chosen_names)}")
    print(f"Number selected: {len(chosen_names)} / {t}")
    print("All faults covered? YES" if covered.sum() == m else "All faults covered? NO")
    print()


# ------------------ Mode 3: Case-1 vs Case-2 (Weak n×1 justification) ------------------


def read_collection(label: str) -> np.ndarray:
    print(f"\n--- Enter vectors for {label} ---")
    return read_real_vectors()


def analyze_collection(V: np.ndarray, tol: float):
    k, d = V.shape
    r = matrix_rank(V, tol)
    return {
        "k": k,
        "d": d,
        "rank": r,
        "independent": (r == k),
        "max_indep": min(k, d),
    }


def mode_weak_nx1_choice():
    print(
        "\n=== Mode 3: Choose Between Two Test Collections (Weak n×1, linear boundaries) ==="
    )
    print("We compare Case-1 vs Case-2 using linear independence / rank.")
    print("In R^4 with linear boundaries, higher rank typically means the collection")
    print("covers more independent directions (less redundancy), which is preferred.\n")

    tol = get_float("Enter tolerance for rank test (typical: 1e-10): ", min_value=0.0, default=1e-10)

    V1 = read_collection("Case-1")
    V2 = read_collection("Case-2")

    a1 = analyze_collection(V1, tol)
    a2 = analyze_collection(V2, tol)

    rows = [
        ["Case-1", a1["d"], a1["k"], a1["rank"], "YES" if a1["independent"] else "NO"],
        ["Case-2", a2["d"], a2["k"], a2["rank"], "YES" if a2["independent"] else "NO"],
    ]
    print("\nSummary:")
    print(
        tabulate(
            rows,
            headers=["Case", "Dimension d", "#Vectors k", "Rank", "Independent?"],
            tablefmt="grid",
        )
    )

    # Recommendation logic
    # Primary: higher rank (covers more independent directions)
    # Secondary: if same rank, prefer fewer vectors (less cost) if both reach that rank.
    rec = None
    justification = []

    if a1["rank"] > a2["rank"]:
        rec = "Case-1"
        justification.append(
            "Case-1 has higher rank → spans more independent directions."
        )
    elif a2["rank"] > a1["rank"]:
        rec = "Case-2"
        justification.append(
            "Case-2 has higher rank → spans more independent directions."
        )
    else:
        # same rank
        if a1["k"] < a2["k"]:
            rec = "Case-1"
            justification.append(
                "Both have same rank; Case-1 uses fewer vectors → less redundant / lower test cost."
            )
        elif a2["k"] < a1["k"]:
            rec = "Case-2"
            justification.append(
                "Both have same rank; Case-2 uses fewer vectors → less redundant / lower test cost."
            )
        else:
            rec = "Either"
            justification.append(
                "Both have same rank and same size; they are equivalent by this criterion."
            )

    print(f"\nRecommendation: {rec}")
    print("Justification (linear independence):")
    for j in justification:
        print(f"  - {j}")

    # Helpful extra text for the “justify” part:
    print("\nSuggested write-up sentence:")
    if rec == "Either":
        print(
            '  "Both collections have the same rank in R^d, so they span the same number of independent directions;'
        )
        print(
            '   therefore neither dominates the other under weak n×1 with linear boundaries."'
        )
    else:
        print(
            f'  "I would choose {rec} because its vectors have a higher rank (greater linear independence),'
        )
        print(
            "   meaning the tests exercise more independent directions in the input space;"
        )
        print(
            '   with linear boundaries in R^4, this reduces redundancy and better supports weak n×1."'
        )
    print()


# ------------------ Main ------------------


def main():
    print("=== Vector & Test-Selection Toolkit (CLI) ===\n")
    while True:
        print("Choose a mode:")
        print("  [1] Check if vectors are linearly independent (real vectors)")
        print("  [2] Minimum tests to cover all faults (binary coverage vectors)")
        print(
            "  [3] Case-1 vs Case-2 choice for weak n×1 (rank/independence justification)"
        )
        print("  [0] Exit\n")

        choice = input("Enter choice: ").strip()
        if choice == "1":
            mode_linear_independence()
        elif choice == "2":
            mode_min_tests_cover_faults()
        elif choice == "3":
            mode_weak_nx1_choice()
        elif choice == "0":
            print("\nGoodbye.")
            break
        else:
            print("Invalid choice. Please enter 0, 1, 2, or 3.\n")


if __name__ == "__main__":
    main()
