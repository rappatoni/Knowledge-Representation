#!/usr/bin/env python
"""
sudoku_sat_solver.py
"""

import sys
import re
import time
import getopt
import fileinput
import itertools
from pprint import pprint
from math import sqrt
from subprocess import call

COMMAND = 'minisat %s %s > %s'
LOGFILE = "minisat.log"
DIMACS_OUT = "dimacs_clauses.txt"
MINISAT_OUT = "minisat_out.txt"
VALID_OUT = "valid_clauses.txt"

help_message = '''[options]
Options:
    -h --help           This help
    -p --problem file   Problem to be converted to sat.
    -t --train file     Train and Train a sat.
'''


def split_list(a_list):
    half = len(a_list) // 2
    return a_list[:half], a_list[half:]


def v(i, j, d):
    return 81 * (i - 1) + 9 * (j - 1) + d


def v_inv(variable):
    variable -= 1
    i = variable // 81 + 1
    remainder = variable % 81
    j = remainder // 9 + 1
    remainder = variable % 9
    d = remainder + 1
    return i, j, d


# Reduces Sudoku problem to a SAT clauses
def valid(cells):
    res = []
    for i, xi in enumerate(cells):
        for j, xj in enumerate(cells):
            if i < j:
                for d in range(1, 10):
                    res.append([-v(xi[0], xi[1], d), -v(xj[0], xj[1], d)])
    return res


def valid_cells():
    res = []
    for i in range(1, 10):
        for j in range(1, 10):
            # denotes (at least) one of the 9 digits (1 clause)
            res.append([v(i, j, d) for d in range(1, 10)])
    return res


def unique_cells():
    res = []
    for i in range(1, 10):
        for j in range(1, 10):
            # does not denote two different digits at once (36 clauses)
            for d in range(1, 10):
                for dp in range(d + 1, 10):
                    res.append([-v(i, j, d), -v(i, j, dp)])
    return res


def valid_rows():
    res = []
    for i in range(1, 10):
        for d in range(1, 10):
            res.append([v(i, j, d) for j in range(1, 10)])
    return res


def valid_columns():
    res = []
    for i in range(1, 10):
        for d in range(1, 10):
            res.append([v(j, i, d) for j in range(1, 10)])
    return res


def valid_blocks():
    res = []
    for i in 1, 4, 7:
        for j in 1, 4, 7:
            for d in range(1, 10):
                res.append([v(i + k % 3, j + k // 3, d) for k in range(9)])
    return res


def unique_rows():
    res = []
    for i in range(1, 10):
        res += valid([(i, j) for j in range(1, 10)])
    return res


def unique_columns():
    res = []
    for i in range(1, 10):
        res += valid([(j, i) for j in range(1, 10)])
    return res


def unique_blocks():
    # ensure 3x3 sub-grids "regions" have distinct values
    res = []
    for i in 1, 4, 7:
        for j in 1, 4, 7:
            res += valid([(i + k % 3, j + k // 3) for k in range(9)])
    return res


def sudoku_clauses():  # this is the "efficient" encoding
    res = []
    res += valid_cells()
    res += unique_cells()
    res += unique_rows()
    res += unique_columns()
    res += unique_blocks()

    assert len(res) == 81 * (1 + 36) + 27 * 324
    return res


def extended_sudoku_clauses():  # extended encoding
    res = []
    res += valid_cells()
    res += unique_cells()
    # ensure rows and columns have distinct values (alldifferent constraints)
    # (2*9*9*9C2 clauses)
    # + redundant constraint: ensure each value appears at least once per columns/row
    # (2*9*9 clauses)
    res += valid_rows()
    res += unique_rows()
    res += valid_columns()
    res += unique_columns()
    # ensure 3x3 sub-grids "regions" have distinct values (alldifferent)
    # (9*9*9C2 clauses)
    # +redundant constraint: each value appears at least once per 3x3 box
    # (9*9 clauses)
    res += valid_blocks()
    res += unique_blocks()

    assert len(res) == 81 * (1 + 36) + 27 * 324 + 3 * 81
    return res


def clause_sets(clause_constructor):
    # this is to transform the entries of a dictionary into sets
    # of strings for comparison with the valid clauses
    clauses = set(frozenset(clause) for clause in clause_constructor)
    return clauses


def extended_sudoku_clauses_with_cats():
    # I decided to keep things separate so as to not break anything. However, we might
    # consider using set/tuple data structures generally because of the faster lookup
    # speed.
    validcells = clause_sets(valid_cells())
    uniquecells = clause_sets(unique_cells())
    validrows = clause_sets(valid_rows())
    uniquerows = clause_sets(unique_rows())
    validcolumns = clause_sets(valid_columns())
    uniquecolumns = clause_sets(unique_columns())
    validblocks = clause_sets(valid_blocks())
    uniqueblocks = clause_sets(unique_blocks())
    res = dict({"vcell": validcells, "ucell": uniquecells,
                "vrow": validrows, "urow": uniquerows,
                "vcol": validcolumns, "ucol": uniquecolumns,
                "vblock": validblocks, "ublock": uniqueblocks})

    return res


def minimal_sudoku_clauses_with_cats():
    validcells = clause_sets(valid_cells())
    uniquerows = clause_sets(unique_rows())
    uniquecolumns = clause_sets(unique_columns())
    uniqueblocks = clause_sets(unique_blocks())
    res = dict({"vcell": validcells, "urow": uniquerows,
                "ucol": uniquecolumns, "ublock": uniqueblocks})

    return res


def efficient_sudoku_clauses_with_cats():
    validcells = clause_sets(valid_cells())
    uniquecells = clause_sets(unique_cells())
    uniquerows = clause_sets(unique_rows())
    uniquecolumns = clause_sets(unique_columns())
    uniqueblocks = clause_sets(unique_blocks())

    res = dict({"vcell": validcells, "ucell": uniquecells, "urow": uniquerows,
                "ucol": uniquecolumns, "ublock": uniqueblocks})

    return res


def minimal_sudoku_clauses():  # minimal Sukoku Encoding
    res = []
    res += valid_cells()
    res += unique_rows()
    res += unique_columns()
    res += unique_blocks()

    assert len(res) == 81 + 27 * 324
    return res


def redundant_sudoku_clauses():  # Add the following redundant constraints:
    # Cardinality Matrix:
    # Block/Row-Interaction:
    # Block/Column-Interaction:
    # There is exactly one value that appears once in every cross of rows/columns:
    # Any two boxes that share the same columns or rows; any two columns and any two rows cannot be identical
    # There can be at most 3 diagonally neighbouring cells with identical values.
    # The (center) diagonals have at least three different values.
    pass


def read_sudoku(sudoku_as_line):
    instance_clauses = []

    i = 1
    j = 1
    for character in sudoku_as_line:
        if character == "\n":
            break
        d = int(character)
        if d:
            instance_clauses.append([v(i, j, d)])
        j = j + 1
        if j > 9:
            i = i + 1
            j = 1
    return instance_clauses


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def dimacs_out(filename, clauses):
    with open(filename, "w") as fileobj:
        for clause in clauses:
            line = " ".join([str(literal) for literal in clause]) + " 0\n"
            fileobj.write(line)


def read_results(ret, output_file, logfile):
    # we don't really care about the output_file
    sat = False
    solution = []
    with open(output_file, "r") as out_file:
        out_file_list = list(out_file)
        if (out_file_list[0] == "SAT\n"):
            sat = True
            for variable in [int(x) for x in out_file_list[1].strip().split()]:
                # 0 is the end
                if variable == 0:
                    continue
                solution.append(variable)
    # we extract the learnt clauses
    learnt = set()
    import re
    with open(logfile, "r") as out_file:
        for line in out_file:
            if line == "clause_found\n":
                clause = next(out_file).strip()
                clause = re.sub(r" -?0", "", clause)
                clause = re.sub(r"^-?0 ", "", clause)
                learnt.add(frozenset([int(x) for x in clause.strip().split()]))
    return sat, frozenset(solution), learnt

def negate(clause):
    return [[-x] for x in clause]

def is_clause_valid(clause, base_clauses):
    negated_clauses = negate(clause)
    add_to_base_dimacs(negated_clauses)
    ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
    satisfied, _ , _ = read_results(ret, MINISAT_OUT, LOGFILE)
    # if we found a clause which is not satisfiable - Success!
    remove_x_lines_from_base_dimacs(number_of_lines=len(negated_clauses))
    if not satisfied:
        return True
    return False

def check_validity(learnt, base_clauses):
    start_time = time.time()
    valid_clauses = set()
    for learn in learnt:
        # for each learnt clause we are interested in if it is a globally valid clause.
        # when we negate a clause, we get many conjuncted clauses
        if is_clause_valid(learn, base_clauses):
            valid_clauses.add((learn, 0))

    end_time = time.time()
    print("validity checking (including pruning): {}".format(end_time - start_time))
    return valid_clauses


def logically_prune(learned_clauses, solutions, base_clauses_with_cats):
    """

    :param learned_clauses: a set of sets of learned clauses from n runs on n different Sudokus
    :return: the logically pruned set of learned clauses
    """
    start_time = time.time()
    # Delete duplicate clauses.
    valid_clauses = set()
    print("start={}".format(len(learned_clauses)))
    # delete unit clauses
    learned_clauses = [clause for clause in learned_clauses if len(clause) >= 2]
    # check if clause is satisfied for all known sudoku solutions
    need_processing = set()
    for clause in learned_clauses:
        for solution in solutions:
            satisfied = False
            for variable in clause:
                if variable in solution:
                    satisfied = True
                    break
            if not satisfied:
                break
        if satisfied:
            need_processing.add(clause)
    # remove already known valid clauses
    needz_processing = set()
    for clause in need_processing:
        next_clause = False
        for key in base_clauses_with_cats:
            for baseclause in base_clauses_with_cats[key]:
                if baseclause.issubset(clause):
                    valid_clauses.add((clause,baseclause))
                    next_clause = True
                    break
            if next_clause:
                break
        if not next_clause:
            needz_processing.add(clause)

    need_processing = set()
    for clause in needz_processing:
        if not (len([int(literal) <= 0 for literal in clause]) == 1 or len([int(literal) <= 0 for literal in clause]) == 0 and len(clause) <= 9):
            need_processing.add(clause)
    print("end={}".format(len(need_processing)))

    end_time = time.time()
    print("pruning: {}".format(end_time - start_time))

    return valid_clauses, need_processing


def prune_validities(valid_clauses, base_clauses):
    """
    :param valid_clauses: set of frozensets
    :return: pruned set of frozensets
    """
    # This function should bring down the number of valid clauses. Some of them might be redundant in the sense
    # that they are supersets of a "core" validity. E.g. if (a, -b, -c, d) and (e, -b,-c,f) and (-b,-c) are
    # in the set of valid clauses then it seems very likely that (-b,-c) is the "core validity and the other two
    # can be removed. So this function should loop over the validities by length starting with the shortest and
    # for each validity, check for its supersets. The supersets should then be removed.
    # This approach may be to radical but for now I would do it this way, can be adjusted if needed.
    kernel = set()
    for clause, base in valid_clauses:
        if not base:
            kernel.update(essential_check(clause, base_clauses))
        else:
            kernel.add(base)
    print("valid_clauses={}".format(len(valid_clauses)))
    print("valid_kernel={}".format(len(kernel)))
    return kernel

def heuristically_prune(learned_clauses):
    """

    :param learned_clauses: a set of sets of learned clauses from n runs on n different Sudokus
    :return: the heuristically pruned set of learned clauses
    """

    # If logical pruning is insufficient we could prune heuristically. If we hardly ever learn a
    # clause, it in all likelihood would not help the SAT-solver much (this is itself a hypothesis
    # we could possibly test). Thus we could throw out all clauses that appear at a rate of less
    # than x/n, where n is the number of sudokus.
    pass


def classify_validities(base_clauses_with_cats, valid_clauses):
    """
    :param base_clauses_with_cats: a ditionary with classes as keys and sets of sets as values
    :param valid_clauses: the set of valid_clauses
    :return: A set of classes of validities
    """
    # type of valid_clauses: set of strings. Strings need to be transformed since they are horrible for
    # comparison. Goal: set of frozensets (frozensets are hashable).
    # type of base clauses should be a dictionary with sets of frozensets as values and categories as keys
    # Create classes with base clauses, then compare.
    # The data structure of the base clauses should be a set of frozensets since that's fastest
    # (for list lookup time is proportional to the list's length). Frozensets are hashable, lists are not.
    # final data structure should contain valid clause, base clause, class.


    # Initializing the dictionary of categories and a flip variable
    cats = ["vcell", "ucell", "vrow", "urow", "vcol", "ucol", "vblock", "ublock", "new"]
    valid_dict = {cat: [] for cat in cats}
    # Comparing valid clauses and base clauses
    for clause in valid_clauses:
        is_new_type = True
        for key in base_clauses_with_cats:
            for baseclause in base_clauses_with_cats[key]:
                if baseclause.issubset(clause):
                    valid_dict[key].append((clause, baseclause))
                    is_new_type = False
        if is_new_type:
            valid_dict["new"].append((clause, 0))
    return valid_dict

def essential_check(clause_to_check, base_clauses):
    essential = set()
    not_essential = set()
    clause = frozenset(clause_to_check)

    comb = [frozenset(x) for x in itertools.combinations(clause, len(clause)-1)]

    for subset_clause in comb:
        if is_clause_valid(subset_clause, base_clauses):
            not_essential.update(clause.difference(subset_clause))

    essential.update(clause.difference(not_essential))
    essential = frozenset(essential)
    not_essential = frozenset(not_essential)

    found_smallest = False
    smallest_clauses = set()
    for i in range(0, len(not_essential)):
        comb = [frozenset(x) for x in itertools.combinations(not_essential, i)]
        for subset_clause in comb:
            check_clause = frozenset(essential.union(subset_clause))
            if is_clause_valid(check_clause, base_clauses):
                found_smallest = True
                smallest_clauses.add(check_clause)
        if found_smallest:
            break
    return smallest_clauses

def get_number_decisions():
    pattern = re.compile("decisions")
    for i, line in enumerate(open('minisat.log')):
        for match in re.finditer(pattern, line):
            result = re.search('decisions             : (.*)       ', line)
            return int(result.group(1))

def decode_clause(clause):
    row, column = 10, 10;
    new_sudoku = [[0 for x in range(1,row)] for y in range(1,column)]

    for literal in clause.split():
        i, j, d = v_inv(abs(int(literal)))
        new_sudoku[i-1][j-1] = d

    b = [variable for row in new_sudoku for variable in row]
    sudoku = ''.join(str(e) for e in b)
    print(sudoku)

def process_sudokus(list_of_sudokus):
    start_time = time.time()
    no_decisions = 0
    learnt_clauses = set()
    solutions = set()
    for index, sudoku in enumerate(list_of_sudokus):
        instance_clauses = read_sudoku(sudoku)
        # solve using MiniSAT
        add_to_base_dimacs(instance_clauses)
        ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
        satisfied, solution, learnt = read_results(ret, MINISAT_OUT, LOGFILE)
        if not satisfied:
            raise Exception("All sudokus should be satisfiable")
        if learnt:
            learnt_clauses.update(learnt)
        remove_x_lines_from_base_dimacs(number_of_lines=len(instance_clauses))
        solutions.add(solution)
        no_decisions = no_decisions + get_number_decisions()

    end_time = time.time()
    print("processing batch of len={}, time={}".format(len(list_of_sudokus), end_time - start_time))
    return learnt_clauses, solutions, no_decisions

def get_batches(number_of_batches, length_of_list):
    batches = []
    for batch_number in range(number_of_batches):
        start_partition = int((batch_number / float(number_of_batches)) * length_of_list)
        end_partition = int(((batch_number + 1) / float(number_of_batches)) * length_of_list)
        batches.append((start_partition, end_partition))
    return batches

def create_base_dimacs(clauses):
    dimacs_out(filename=DIMACS_OUT, clauses=clauses)

def add_to_base_dimacs(clauses):
    with open(DIMACS_OUT, "a") as fileobj:
        for clause in clauses:
            line = " ".join([str(literal) for literal in clause]) + " 0\n"
            fileobj.write(line)

def remove_x_lines_from_base_dimacs(number_of_lines):
    with open(DIMACS_OUT, "r") as fileobj:
        lines = fileobj.readlines()
        lines = lines[:-number_of_lines]
    with open(DIMACS_OUT, "w") as fileobj:
        fileobj.writelines(lines)

def write_validities_to_file(interval_from, interval_to, encoding, validities, batch_size):
    filename = "_".join([str(interval_from),
                        str(interval_to),
                        encoding,
                        "batch_size",
                        str(batch_size),
                        "validities.txt"
                        ])
    with open(filename, "w+") as fileobj:
        for clause in validities:
            line = " ".join([str(literal) for literal in clause]) + "\n"
            fileobj.write(line)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    opts, args = getopt.getopt(argv[1:], "hp:t:l:b:i:v:",
    ["help", "problem", "train", "limit", "batch", "interval", "validities"])

    # option processing
    batch = 1
    limit = 0
    interval_from = 0
    interval_to = 0
    validities = set()
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-l", "--limit"):
            limit = int(value)
        if option in ("-b", "--batch"):
            batch = int(value)
        if option in ("-i", "--interval"):
            values = [int(x) for x in value.strip().split(":")]
            print(values)
            interval_from, interval_to = values[0], values[1]
        if option in ("-t", "--train", "-p", "--problem"):
            with open(value) as fileobj:
                file_as_list = list(fileobj)
        if option in ("-v", "--validities"):
            with open(value) as fileobj:
                lines = fileobj.readlines()
                for line in lines:
                    validities.add(frozenset(line.strip().split()))
    if limit:
        interval_to = limit
    if not interval_to:
        interval_to = len(file_as_list)
    file_as_list = file_as_list[interval_from:interval_to]
    print("interval_from={}, interval_to={}".format(interval_from, interval_to))
    print("limit={}".format(limit))
    print("batch={}".format(batch))

    #base_clauses = sudoku_clauses()
    base_clauses = extended_sudoku_clauses()
    #base_clauses = minimal_sudoku_clauses()
    encoding = "minimal"
    create_base_dimacs(base_clauses)
    if validities:
        add_to_base_dimacs(validities)

    for option, value in opts:
        base_clauses_with_cats = extended_sudoku_clauses_with_cats()
        if option in ("-t", "--train"):
            solutions = set()

            print("Training:")
            global_validities = set()

            for start_partition, end_partition in get_batches(number_of_batches=batch, length_of_list=len(file_as_list)):
                learnt_clauses, new_solutions, _ = process_sudokus(file_as_list[start_partition:end_partition])
                solutions.update(new_solutions)

                valid_clauses = set()
                valid_clauses_pruned, need_processing = logically_prune(learnt_clauses, solutions, base_clauses_with_cats)
                valid_clauses.update(valid_clauses_pruned)
                print("Checking Validities")
                new_valid_clauses = check_validity(need_processing, base_clauses)
                valid_clauses.update(new_valid_clauses)
                print("Pruning Validities")
                valid_clauses_kernel = prune_validities(valid_clauses, base_clauses)
                global_validities.update(valid_clauses_kernel)
                add_to_base_dimacs(valid_clauses_kernel)

            print("Classifying Validities")
            classified_validities = classify_validities(base_clauses_with_cats=base_clauses_with_cats,
                                                        valid_clauses=global_validities)
            for key in classified_validities:
                print("key={}, len={}".format(key, len(classified_validities[key])))
                if key == "new" and len(classified_validities[key]) > 0:
                    print(classified_validities[key])
            write_validities_to_file(interval_from, interval_to, encoding, global_validities, batch)

        if option in ("-p", "--problem"):
            # iterate over the set of sudoku problems
            learnt_clauses, solutions, no_decisions = process_sudokus(file_as_list)
            print("number of decisions = {}".format(no_decisions))


if __name__ == "__main__":
    sys.exit(main())
