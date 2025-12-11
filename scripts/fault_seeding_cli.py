#!/usr/bin/env python3
"""
Fault Seeding (Mills) CLI Tool

Features:
  1) Estimate total and remaining real faults N, N-n from seeding data (ratio).
  2) Compute confidence level C for a claim "at most N real faults"
     AFTER all seeded faults are found (simple Mills formula).
  3) Compute required number of seeded faults S for a target confidence C.
  4) Compute confidence level C using the combination / hypergeometric
     formula WHILE we are still looking for all the seeded faults.
"""

import math


# ---------- General input helpers ----------

def get_float(prompt: str, min_value=None, max_value=None):
    """Prompt for a float with optional bounds."""
    while True:
        s = input(prompt).strip()
        try:
            x = float(s)
        except ValueError:
            print("  Please enter a numeric value.")
            continue

        if min_value is not None and x < min_value:
            print(f"  Value must be >= {min_value}.")
            continue
        if max_value is not None and x > max_value:
            print(f"  Value must be <= {max_value}.")
            continue
        return x


def get_int(prompt: str, min_value=None, max_value=None):
    """Prompt for an integer with optional bounds."""
    while True:
        s = input(prompt).strip()
        try:
            x = int(s)
        except ValueError:
            print("  Please enter an integer value.")
            continue

        if min_value is not None and x < min_value:
            print(f"  Value must be >= {min_value}.")
            continue
        if max_value is not None and x > max_value:
            print(f"  Value must be <= {max_value}.")
            continue
        return x


def comb(n: int, k: int) -> int:
    """Safe wrapper around math.comb with basic checks."""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


# ---------- Mode 1: estimate N & remaining faults ----------

def mode_estimate_N():
    """
    Mode 1:
      Estimate total real faults N and remaining faults N - n
      using s/S = n/N  (simple Mills ratio).
    """
    print("\n--- Mode 1: Estimate total and remaining real faults (simple ratio) ---")
    print("Assumption: Detection rate of seeded and real faults is the same:")
    print("    s / S = n / N  =>  N = S * n / s\n")

    S = get_int("Enter total seeded faults S: ", min_value=1)
    s = get_int("Enter detected seeded faults s: ", min_value=0, max_value=S)
    n = get_int("Enter detected real (non-seeded) faults n: ", min_value=0)

    if s == 0:
        print("\nCannot estimate N because no seeded faults were detected (s=0).")
        print("The ratio s/S = n/N is undefined when s = 0.\n")
        return

    N_est = (S * n) / s
    remaining = N_est - n

    print("\nEstimated total real faults N (Mills assumption):")
    print(f"  N ≈ {N_est:.3f}")
    print(f"Estimated remaining real faults N - n:")
    print(f"  N - n ≈ {remaining:.3f}\n")


# ---------- Mode 2: confidence after all seeds found ----------

def mode_confidence():
    """
    Mode 2:
      Compute confidence level C for a claim "there are at most N real faults",
      given that we seeded S faults and found all of them, and observed n real faults.
    """
    print("\n--- Mode 2: Confidence level for a claim on N (Mills, all seeds found) ---")
    print("You claim: 'The system has at most N real (non-seeded) faults.'")
    print("You seed S faults, test until ALL S seeded faults are found,")
    print("and during this process you find n real faults.\n")
    print("Mills formula (lecture):")
    print("  If n ≤ N:  C = S / (S + N + 1)")
    print("  If n > N:  C = 1 (your claim N is already violated)\n")

    N = get_int("Enter claimed upper bound on real faults N (e.g., 0, 1, 10): ",
                min_value=0)
    S = get_int("Enter total seeded faults S: ", min_value=1)
    n = get_int("Enter number of real faults n found while finding all S: ",
                min_value=0)

    if n > N:
        C = 1.0
        print("\nYou already found more real faults than your claimed bound N.")
        print("So the probability that 'there are at most N faults' is effectively 0,")
        print("and the probability that 'N is too small' is 1.\n")
    else:
        C = S / (S + N + 1)
        print("\nUsing Mills formula with n ≤ N:")
        print(f"  C = S / (S + N + 1) = {S} / ({S} + {N} + 1)")
        print(f"  C ≈ {C:.4f}  (i.e., {C*100:.2f}% confidence)\n")

    print(f"Computed confidence level C ≈ {C:.4f}  ({C*100:.2f}%)\n")


# ---------- Mode 3: required S for target C ----------

def mode_required_S():
    """
    Mode 3:
      Given target confidence C and claimed N, compute required S:
        C = S / (S + N + 1)  =>  S = C (N+1) / (1 - C)
    """
    print("\n--- Mode 3: Required seeded faults S for target confidence ---")
    print("We want: 'How many seeded faults S do we need to claim")
    print("at most N real faults with confidence at least C?'")
    print("\nFrom Mills:")
    print("  C = S / (S + N + 1)  (assuming n ≤ N)")
    print("  ⇒  S = C (N + 1) / (1 - C)\n")
    print("Special case N = 0 (fault-free claim):  S = C / (1 - C)\n")

    N = get_int("Enter claimed upper bound on real faults N (e.g., 0): ",
                min_value=0)
    C = get_float("Enter required confidence C (0 < C < 1, e.g., 0.98): ",
                  min_value=0.0, max_value=1.0)

    if C <= 0.0 or C >= 1.0:
        print("\nC must be strictly between 0 and 1 for this formula.\n")
        return

    S_real = C * (N + 1) / (1.0 - C)
    S_int = math.ceil(S_real)

    print("\nRequired seeded faults (real-valued):")
    print(f"  S = C (N + 1) / (1 - C) = {C:.4f} * ({N} + 1) / (1 - {C:.4f})")
    print(f"  S ≈ {S_real:.3f}")
    print("Rounded up to an integer number of seeded faults:")
    print(f"  S_required = {S_int} seeded faults\n")


# ---------- Mode 4: partial confidence using combination formula ----------

def mills_confidence_partial(S: int, s: int, N: int, n: int) -> float:
    """
    Compute Mills confidence using the exact combination formula:

        C = ( C(S, s-1) ) / ( C(S+N+1, N+s) )    if n <= N
        C = 1                                    if n > N

    """
    # If we already exceeded N actual faults, claim "at most N" is falsified
    if n > N:
        return 1.0

    # s must be >= 1 for the formula C(S, s-1)
    if s <= 0:
        # interpret "haven't found any seeded faults yet" → zero confidence
        return 0.0

    from math import comb

    numerator = comb(S, s - 1)
    denominator = comb(S + N + 1, N + s)

    if denominator == 0:
        return 0.0  # degenerate but safe

    C = numerator / denominator

    # Clamp for safety
    C = max(0.0, min(1.0, C))
    return C


def mode_partial_confidence():
    """
    Mode 4:
      Use the combination / hypergeometric-style formula from your slide
      to compute confidence while we are *still* finding seeded faults.
    """
    print("\n--- Mode 4: Partial-progress confidence (combination formula) ---")
    print("This mode is for the case where we have NOT yet found all S seeded faults.")
    print("Inputs:")
    print("  S = total seeded faults inserted")
    print("  s = seeded faults detected so far (s < S is the interesting case)")
    print("  N = claimed upper bound on real faults")
    print("  n = real (non-seeded) faults detected so far\n")
    print("The formula from your 'Fault seeding (Mills): expressing confidence (4)'")
    print("slide uses binomial coefficients C(a, b). In the code, those are")
    print("implemented using comb(a, b).\n")

    S = get_int("Enter total seeded faults S: ", min_value=1)
    s = get_int("Enter detected seeded faults so far s: ",
                min_value=0, max_value=S)
    N = get_int("Enter claimed upper bound on real faults N: ",
                min_value=0)
    n = get_int("Enter detected real (non-seeded) faults so far n: ",
                min_value=0)

    C = mills_confidence_partial(S, s, N, n)

    print("\n[WARNING] The math inside mills_confidence_partial() is currently")
    print("a placeholder. Replace it with the exact combination formula from")
    print("your ECE 322 slides to get correct values.\n")

    print(f"Computed (placeholder) confidence C ≈ {C:.4f}  ({C*100:.2f}%)\n")


# ---------- Main menu ----------

def main():
    print("=== Fault Seeding (Mills) CLI Tool ===")
    print("Helps you:")
    print("  1) Estimate total & remaining real faults from seeding data.")
    print("  2) Compute confidence for a claim 'at most N faults' after all seeds found.")
    print("  3) Compute required seeded faults S for a desired confidence.")
    print("  4) (Advanced) Confidence using combinational formula before all seeds found.\n")

    while True:
        print("Select mode:")
        print("  [1] Estimate N and remaining faults (simple ratio s/S = n/N)")
        print("  [2] Confidence C for a claim on N (Mills, all seeds found)")
        print("  [3] Required S for target confidence C and claim N")
        print("  [4] Partial-progress confidence C using combination formula")
        print("  [0] Exit\n")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            mode_estimate_N()
        elif choice == "2":
            mode_confidence()
        elif choice == "3":
            mode_required_S()
        elif choice == "4":
            mode_partial_confidence()
        elif choice == "0":
            print("\nGoodbye.")
            break
        else:
            print("Invalid choice. Please enter 0, 1, 2, 3, or 4.\n")


if __name__ == "__main__":
    main()
