#!/usr/bin/env python3

from allpairspy import AllPairs
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


def get_parameters():
    """Interactively get parameter names and their possible values."""
    num_params = get_int("Enter number of parameters (columns): ")

    param_names = []
    param_values = []

    print("\nNow enter the name and possible values for each parameter.")
    print("Example values input: red, blue, green\n")

    for i in range(num_params):
        name = input(f"Name for parameter {i + 1} (e.g., Color): ").strip()
        if not name:
            name = f"Param{i + 1}"

        while True:
            values_str = input(f"Possible values for {name} (comma-separated): ").strip()
            values = [v.strip() for v in values_str.split(",") if v.strip()]
            if len(values) < 1:
                print("You must provide at least one value.")
            else:
                break

        param_names.append(name)
        param_values.append(values)

    return param_names, param_values


def get_invalid_pairs():
    """
    Let the user enter invalid pairs of values like:
      red, small
    until they type 'E' or 'e'.
    """
    invalid_pairs = set()

    print("\n--- Invalid pair constraints (optional) ---")
    print("Enter pairs of values that must NEVER appear together in a test case.")
    print("Format: value1, value2")
    print("Example: red, small")
    print("Type 'E' and press Enter when you are done.\n")

    while True:
        s = input("Enter invalid pair (or 'E' to finish): ").strip()
        if s.upper() == "E":
            break

        parts = [p.strip() for p in s.split(",")]
        if len(parts) != 2:
            print("Please enter exactly two values separated by a comma (e.g., red, small).")
            continue

        v1, v2 = parts
        if not v1 or not v2:
            print("Both values must be non-empty.")
            continue

        invalid_pairs.add((v1, v2))

    if invalid_pairs:
        print("\nInvalid pairs recorded:")
        for v1, v2 in invalid_pairs:
            print(f"  - ({v1}, {v2})")
    else:
        print("\nNo invalid pairs specified.")

    return invalid_pairs


def make_filter_func(invalid_pairs):
    """
    Create a filter function compatible with AllPairs.
    The function will return False for any combination that includes
    one of the invalid value pairs (in any order).
    """

    # For faster membership checks, include both (v1, v2) and (v2, v1)
    normalized_pairs = set()
    for (v1, v2) in invalid_pairs:
        normalized_pairs.add((v1, v2))
        normalized_pairs.add((v2, v1))

    def is_valid_combination(row):
        """
        row is a list representing a (possibly partial) test case.
        AllPairs calls this many times with partially-filled rows.
        We just need to ensure no complete pair of values in the row
        matches one of our invalid pairs.
        """
        # Filter out None (for partial rows)
        present_values = [v for v in row if v is not None]

        # Check all distinct pairs in the current row
        n = len(present_values)
        for i in range(n):
            for j in range(i + 1, n):
                if (present_values[i], present_values[j]) in normalized_pairs:
                    return False
        return True

    return is_valid_combination


def generate_pairwise(param_values, invalid_pairs):
    """Generate pairwise test cases using AllPairs and an optional filter."""
    if invalid_pairs:
        filter_func = make_filter_func(invalid_pairs)
        pairs = list(AllPairs(param_values, filter_func=filter_func))
    else:
        pairs = list(AllPairs(param_values))

    return pairs


def main():
    print("=== Pairwise Test Case Generator (CLI) ===\n")

    # 1. Get parameters & their values
    param_names, param_values = get_parameters()

    # 2. Get invalid pair constraints
    invalid_pairs = get_invalid_pairs()

    # 3. Generate pairwise combinations
    print("\nGenerating pairwise test cases...\n")
    test_cases = generate_pairwise(param_values, invalid_pairs)

    if not test_cases:
        print("No valid test cases could be generated. "
              "Check if your constraints are too strict.")
        return

    # 4. Display results as a pretty table
    table_rows = []
    for idx, row in enumerate(test_cases, start=1):
        table_rows.append([idx] + list(row))

    headers = ["Test #"] + param_names

    print(tabulate(table_rows, headers=headers, tablefmt="grid"))

    # 5. Summary
    total_full = 1
    for vals in param_values:
        total_full *= len(vals)

    print(f"\nTotal possible combinations (full Cartesian product): {total_full}")
    print(f"Number of pairwise test cases generated: {len(test_cases)}")


if __name__ == "__main__":
    main()
