#!/usr/bin/env python3
"""
MC/DC (Modified Condition/Decision Coverage) Solver
For ECE 322 - Software Testing and Maintenance

This script automatically:
1. Generates truth tables for boolean expressions
2. Finds MC/DC pairs for each condition
3. Identifies minimal test suites

Author: ECE 322 Student
Date: December 2024
"""

import itertools
import re
from typing import List, Dict, Tuple, Set


class MCDCSolver:
    """
    Solves Modified Condition/Decision Coverage problems for boolean expressions.
    """
    
    def __init__(self, expression: str):
        """
        Initialize with a boolean expression.
        
        Args:
            expression: String containing boolean expression with variables a-z
                       Supports operators: &&, ||, !, (, )
        
        Example:
            solver = MCDCSolver("(a && b) || (c && !d)")
        """
        self.original_expression = expression
        self.expression = self._normalize_expression(expression)
        self.variables = self._extract_variables()
        self.truth_table = []
        self.mcdc_pairs = {}
        
    def _normalize_expression(self, expr: str) -> str:
        """
        Convert expression to Python-evaluable format.
        && → and, || → or, ! → not
        """
        # Replace operators
        expr = expr.replace('&&', ' and ')
        expr = expr.replace('||', ' or ')
        expr = expr.replace('!', ' not ')
        return expr
    
    def _extract_variables(self) -> List[str]:
        """
        Extract unique variable names from expression.
        Returns sorted list of variables.
        """
        # Find all single lowercase letters
        variables = set(re.findall(r'\b[a-z]\b', self.expression))
        return sorted(list(variables))
    
    def generate_truth_table(self) -> List[Dict]:
        """
        Generate complete truth table for the expression.
        Returns list of dicts with test number, variable values, and result.
        """
        num_vars = len(self.variables)
        
        # Generate all 2^n combinations
        for test_num, combination in enumerate(itertools.product([False, True], repeat=num_vars), start=1):
            # Create variable assignments
            var_values = dict(zip(self.variables, combination))
            
            # Evaluate expression
            try:
                    # restrict builtins for safety; expression uses Python keywords
                    result = eval(self.expression, {"__builtins__": None}, var_values)
            except Exception as e:
                print(f"Error evaluating expression: {e}")
                result = None
            
            # Store in truth table
            test_case = {
                'test_num': test_num,
                **var_values,
                'result': result
            }
            self.truth_table.append(test_case)
        
        return self.truth_table
    
    def find_mcdc_pairs(self) -> Dict[str, List[Tuple[int, int]]]:
        """
        Find MC/DC pairs for each variable.
        
        For each variable, finds pairs where:
        1. The variable flips (T→F or F→T)
        2. All other variables stay constant
        3. The overall result changes
        
        Returns dict mapping variable name to list of (test1, test2) pairs.
        """
        if not self.truth_table:
            self.generate_truth_table()
        
        for var in self.variables:
            pairs = []
            
            # Compare each test with every other test
            for i, test1 in enumerate(self.truth_table):
                for j, test2 in enumerate(self.truth_table):
                    if i >= j:  # Avoid duplicates and self-comparison
                        continue
                    
                    # Check if ONLY the target variable differs
                    other_vars_same = all(
                        test1[v] == test2[v] 
                        for v in self.variables if v != var
                    )
                    
                    # Check if target variable flips
                    target_var_flips = test1[var] != test2[var]
                    
                    # Check if result changes
                    result_changes = test1['result'] != test2['result']
                    
                    if other_vars_same and target_var_flips and result_changes:
                        pairs.append((test1['test_num'], test2['test_num']))
            
            self.mcdc_pairs[var] = pairs
        
        return self.mcdc_pairs
    
    def get_minimal_test_suite(self) -> Set[int]:
        """
        Extract minimal test suite that achieves MC/DC coverage.
        
        Returns set of test numbers needed.
        """
        if not self.mcdc_pairs:
            self.find_mcdc_pairs()
        
        test_suite = set()
        
        # Collect all tests from all pairs
        for var, pairs in self.mcdc_pairs.items():
            if pairs:
                # Take first valid pair (could optimize to find absolute minimum)
                test_suite.add(pairs[0][0])
                test_suite.add(pairs[0][1])
        
        return test_suite
    
    def print_truth_table(self):
        """Pretty print the truth table."""
        if not self.truth_table:
            self.generate_truth_table()
        
        print("\n" + "="*80)
        print("TRUTH TABLE")
        print("="*80)
        
        # Header
        header = ["Test"] + self.variables + ["Result"]
        print(f"{'  '.join(f'{h:>6}' for h in header)}")
        print("-" * 80)
        
        # Rows
        for test in self.truth_table:
            row = [str(test['test_num'])]
            row += [str(int(test[v])) for v in self.variables]
            row += [str(int(test['result']))]
            print(f"{'  '.join(f'{item:>6}' for item in row)}")
    
    def print_mcdc_analysis(self):
        """Pretty print MC/DC pair analysis."""
        if not self.mcdc_pairs:
            self.find_mcdc_pairs()
        
        print("\n" + "="*80)
        print("MC/DC PAIR ANALYSIS")
        print("="*80)
        
        for var in self.variables:
            pairs = self.mcdc_pairs[var]
            print(f"\nVariable '{var}':")
            
            if not pairs:
                print("  ⚠️  NO VALID MC/DC PAIRS FOUND!")
                print("  (This variable may not independently affect the outcome)")
            else:
                for idx, (t1, t2) in enumerate(pairs, start=1):
                    print(f"  Pair {idx}: Tests {t1} ↔ {t2}")
                    
                    # Show the actual values
                    test1 = self.truth_table[t1-1]
                    test2 = self.truth_table[t2-1]
                    
                    print(f"    Test {t1}: ", end="")
                    for v in self.variables:
                        print(f"{v}={int(test1[v])} ", end="")
                    print(f"→ {int(test1['result'])}")
                    
                    print(f"    Test {t2}: ", end="")
                    for v in self.variables:
                        print(f"{v}={int(test2[v])} ", end="")
                    print(f"→ {int(test2['result'])}")
    
    def print_minimal_suite(self):
        """Pretty print the minimal test suite."""
        suite = self.get_minimal_test_suite()
        
        print("\n" + "="*80)
        print("MINIMAL TEST SUITE")
        print("="*80)
        
        print(f"\nTests required: {sorted(suite)}")
        print(f"Total: {len(suite)} test cases")
        
        print("\nDetailed test cases:")
        for test_num in sorted(suite):
            test = self.truth_table[test_num-1]
            print(f"\n  Test {test_num}:")
            for var in self.variables:
                print(f"    {var} = {test[var]} ({int(test[var])})")
            print(f"    Result = {test['result']} ({int(test['result'])})")
    
    def solve(self):
        """Complete analysis: generate table, find pairs, show minimal suite."""
        print("\n" + "="*80)
        print(f"MC/DC ANALYSIS FOR: {self.original_expression}")
        print("="*80)
        print(f"Variables detected: {', '.join(self.variables)}")
        print(f"Total combinations: 2^{len(self.variables)} = {2**len(self.variables)}")
        
        self.print_truth_table()
        self.print_mcdc_analysis()
        self.print_minimal_suite()
        
        # Warning for missing coverage
        if any(len(pairs) == 0 for pairs in self.mcdc_pairs.values()):
            print("\n⚠️  WARNING: Some variables have no MC/DC pairs!")
            print("This expression may not satisfy MC/DC criterion fully.")


def main():
    # """
    # Example usage and test cases.
    # """
    # print("="*80)
    # print("MC/DC SOLVER - ECE 322")
    # print("="*80)
    
    # # Example 1: From your exam
    # print("\n\n### EXAMPLE 1: Exam Problem ###")
    # expr1 = "a || ((!b) && c && d)"
    # solver1 = MCDCSolver(expr1)
    # solver1.solve()
    
    # # Example 2: From assignment
    # print("\n\n### EXAMPLE 2: Assignment Problem ###")
    # expr2 = "(a || !b) && (c || (!d && a))"
    # solver2 = MCDCSolver(expr2)
    # solver2.solve()
    
    # # Example 3: Loan approval from earlier
    # print("\n\n### EXAMPLE 3: Loan Approval ###")
    # expr3 = "(a && b) || (c && d)"
    # solver3 = MCDCSolver(expr3)
    # solver3.solve()
    
    # Interactive mode
    print("\n\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("Enter your own boolean expression (or 'quit' to exit)")
    print("Use: a-z for variables, && for AND, || for OR, ! for NOT")
    print("Example: (a && b) || (!c && d)")
    
    while True:
        try:
            user_expr = input("\nEnter expression: ").strip()
            if user_expr.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_expr:
                continue
            
            solver = MCDCSolver(user_expr)
            solver.solve()
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please check your expression syntax.")


if __name__ == "__main__":
    main()