#!/usr/bin/env python
"""
sudoku_sat_solver.py
"""

import sys
import time
import getopt
import fileinput
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
    half = len(a_list)//2
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
    return i,j,d

#Reduces Sudoku problem to a SAT clauses
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
        for d in range(1,10):
            res.append([v(i, j, d) for j in range(1, 10)])
    return res

def valid_columns():
    res = []
    for i in range(1, 10):
        for d in range(1,10):
            res.append([v(j, i, d) for j in range(1, 10)])
    return res

def valid_blocks():
    res = []
    for i in 1, 4, 7:
        for j in 1, 4 ,7:
            for d in range (1,10):
                res.append([v(i+k%3, j+k//3, d) for k in range(9)])
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
        for j in 1, 4 ,7:
            res += valid([(i + k % 3, j + k // 3) for k in range(9)])
    return res

def sudoku_clauses(): #this IS the "efficient" encoding
    res = []
    res += valid_cells()
    res += unique_cells()
    res += unique_rows()
    res += unique_columns()
    res += unique_blocks()

    assert len(res) == 81 * (1 + 36) + 27 * 324
    return res

def extended_sudoku_clauses(): #extended encoding
    res = []
    res += valid_cells()
    res += unique_cells()
    # ensure rows and columns have distinct values (alldifferent constraints)
    #(2*9*9*9C2 clauses)
    # + redundant constraint: ensure each value appears at least once per columns/row
    # (2*9*9 clauses)
    res += valid_rows()
    res += unique_rows()
    res += valid_columns()
    res += unique_columns()
    # ensure 3x3 sub-grids "regions" have distinct values (alldifferent)
    # (9*9*9C2 clauses)
    # +redundant constraint: each value appears at least once per 3x3 box
    #(9*9 clauses)
    res += valid_blocks()
    res += unique_blocks()

    assert len(res) == 81*(1+36)+ 27 * 324+ 3 * 81
    return res

def clause_sets(clause_constructor):
    #this is to transform the entries of a dictionary into sets
    # of strings for comparison with the valid clauses
    clauses=set(frozenset(clause) for clause in clause_constructor)
    return clauses

def extended_sudoku_clauses_with_cats():
    #I decided to keep things separate so as to not break anything. However, we might
    #consider using set/tuple data structures generally because of the faster lookup
    #speed.
    validcells = clause_sets(valid_cells())
    uniquecells=clause_sets(unique_cells())
    validrows=clause_sets(valid_rows())
    uniquerows=clause_sets(unique_rows())
    validcolumns=clause_sets( valid_columns())
    uniquecolumns=clause_sets(unique_columns())
    validblocks=clause_sets(valid_blocks())
    uniqueblocks=clause_sets(unique_blocks())
    res=dict({"vcell":validcells,"ucell":uniquecells,
              "vrow": validrows,"urow": uniquerows,
                "vcol": validcolumns,"ucol": uniquecolumns,
              "vblock": validblocks,"ublock": uniqueblocks})

    # res += {"vcell":valid_cells()}
    # res += {"ucell":unique_cells()}
    # res += {"vrow": valid_rows()}
    # res += {"urow": unique_rows()}
    # res += {"vcol": valid_columns()}
    # res += {"ucol": unique_columns()}
    # res += {"vblock": valid_blocks()}
    # res += {"ublock": unique_blocks()}

    assert len(res) == 81 * (1 + 36) + 27 * 324 + 3 * 81
    return res


def minimal_sudoku_clauses_with_cats():
    validcells = clause_sets(valid_cells())
    uniquerows = clause_sets(unique_rows())
    uniquecolumns = clause_sets(unique_columns())
    uniqueblocks = clause_sets(unique_blocks())
    res = dict({"vcell": validcells, "urow": uniquerows,
                "ucol": uniquecolumns,"ublock": uniqueblocks})

    assert len(res) == 81 + 27 * 324
    return res

def efficient_sudoku_clauses_with_cats():
    validcells = clause_sets(valid_cells())
    uniquecells = clause_sets(unique_cells())
    uniquerows = clause_sets(unique_rows())
    uniquecolumns = clause_sets(unique_columns())
    uniqueblocks = clause_sets(unique_blocks())

    res = dict({"vcell": validcells,"ucell":uniquecells, "urow": uniquerows,
                "ucol": uniquecolumns,"ublock": uniqueblocks})

    assert len(res) == 81 * (1 + 36) + 27 * 324
    return res


def minimal_sudoku_clauses(): #minimal Sukoku Encoding
    res = []
    res += valid_cells()
    res += unique_rows()
    res += unique_columns()
    res += unique_blocks()

    assert len(res) == 81 + 27 * 324
    return res

def redundant_sudoku_clauses(): #Add the following redundant constraints:
    #Cardinality Matrix:
    #Block/Row-Interaction:
    #Block/Column-Interaction:
    #There is exactly one value that appears once in every cross of rows/columns:
    #Any two boxes that share the same columns or rows; any two columns and any two rows cannot be identical
    #There can be at most 3 diagonally neighbouring cells with identical values.
    #The (center) diagonals have at least three different values.
    pass

def read_sudoku(sudoku_as_line, clauses):
    instance_clauses = clauses[:]

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
                learnt.add(clause)
    return sat, solution, learnt

def add_clauses(base, extra_clauses):
    new_clauses = base[:]
    for clause in extra_clauses:
        new_clauses.append([clause])
    return new_clauses

def negate(clause):
    return [-int(x) for x in clause.strip().split()]

def check_validity(learnt, base_clauses):
    valid_clauses = set()
    valid_clauses_pruned, need_processing = logically_prune(learnt)
    valid_clauses.update(valid_clauses_pruned)
    for learn in need_processing:
        # for each learnt clause we are interested in if it is a globally valid clause.
        # when we negate a clause, we get many conjuncted clauses
        negated_clauses = negate(learn)
        instance_clauses = add_clauses(base_clauses, negated_clauses)
        dimacs_out(DIMACS_OUT, instance_clauses)
        ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
        satisfied, solution, learnt_clauses = read_results(ret, MINISAT_OUT, LOGFILE)
        # if we found a clause which is not satisfiable - Success!
        if not satisfied:
            valid_clauses.add(learn)
    return valid_clauses

def logically_prune(learned_clauses):
    """

    :param learned_clauses: a set of sets of learned clauses from n runs on n different Sudokus
    :return: the logically pruned set of learned clauses
    """
    valid_clauses = set()
    print(len(learned_clauses))
    learned_clauses = [clause for clause in learned_clauses if " " in clause]
    print(len(learned_clauses))
    #Delete duplicate clauses.

    #Delete contradictory clauses: if a clause say (a or b) and its negation are both learned we know
    #neither is valid. To do this we use that ~(a or b) <=> (~a & ~b). For every set of learned clauses
    #we collect the unit clauses into a set representing a big conjunction (e.g. (~a & ~b)
    # becomes {~a,~b}). Then we compare all non-unit-clauses of length smaller or equal to
    # the cardinality of any of the unit clause sets to the respective unit clause sets. If all
    #literals of a non-unit-clause appear in negation in a unit clause set, delete the non-unit-clause.

    #Thereafter delete the unit clauses: unit clauses cannot be valid in general Sudokus.

    #Alternative (better) approach: record the sudoku solutions. Then for each clause  say (a or ~b)
    #check the solved sudokus. If there is a solved sudoku s.t. a is not in the solution and b is, then
    # (a or ~b) is false in that sudoku and hence cannot be valid.

    #Check for supersets of encoding clauses (minimal and extended).

    #Delete clauses that were already val-checked on the last iteration (i.e. record known non-validities)

    return valid_clauses, learned_clauses

def heuristically_prune(learned_clauses):
    """

    :param learned_clauses: a set of sets of learned clauses from n runs on n different Sudokus
    :return: the heuristically pruned set of learned clauses
    """

    #If logical pruning is insufficient we could prune heuristically. If we hardly ever learn a
    #clause, it in all likelihood would not help the SAT-solver much (this is itself a hypothesis
    #we could possibly test). Thus we could throw out all clauses that appear at a rate of less
    # than x/n, where n is the number of sudokus.
    pass

def classify_validities(base_clauses_with_cats, valid_clauses):
    """
    :param base_clauses_with_cats: a ditionary with classes as keys and sets of sets as values
    :param valid_clauses: the set of valid_clauses
    :return: A set of classes of validities
    """
    #type of valid_clauses: set of strings. Strings need to be transformed since they are horrible for
    #comparison. Goal: set of frozensets (frozensets are hashable).
    #type of base clauses should be a dictionary with sets of frozensets as values and categories as keys
    #Create classes with base clauses, then compare.
    #The data structure of the base clauses should be a set of frozensets since that's fastest
    #(for list lookup time is proportional to the list's length). Frozensets are hashable, lists are not.
    #final data structure should contain valid clause, base clause, class.


    #Initializing the dictionary of categories and a flip variable
    cats=["vcell","ucell","vrow","urow","vcol","vblock","ublock","new"]
    valid_dict={cat: [] for cat in cats}
    check=0
    #converting valid_clauses into sets
    for clause in valid_clauses:
        frozenset(int(x) for x in clause.strip().split())
    #Comparing valid clauses and base clauses
    for clause in valid_clauses:
        for key in base_clauses_with_cats:
            for baseclause in base_clauses_with_cats[key]:
                if baseclause.issubset(clause):
                    valid_dict[key].append([clause,baseclause])
                    check=1
        if check==0:
            valid_dict["new"].append([clause,baseclause])
    return valid_dict

def process_sudokus(list_of_sudokus, encoding):
    print("Before Training:")
    start_time = time.time()
    learnt_clauses = set()
    for index, sudoku in enumerate(list_of_sudokus):
        print("{} of {}".format(index + 1, len(list_of_sudokus)))
        instance_clauses = read_sudoku(sudoku, encoding)

        #solve using MiniSAT
        dimacs_out(DIMACS_OUT, instance_clauses)
        ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
        satisfied, solution, learnt = read_results(ret, MINISAT_OUT, LOGFILE)
        if not satisfied:
            raise Exception("All sudokus should be satisfiable")
        if learnt:
            for clause in learnt:
                learnt_clauses.add(clause)
    end_time = time.time()
    print("time={}".format(end_time - start_time))
    return learnt_clauses

def write_out_valid_clauses(valid_clauses):
    with open(VALID_OUT, "w+") as fileobj:
        for clause in valid_clauses:
            fileobj.write("clause\n")
            fileobj.write(clause + "\n")
            for variable in clause.split():
                i, j, d = v_inv(abs(int(variable)))
                present = "True"
                if int(variable) < 0:
                    present = "False"
                fileobj.write("i={}, j={}, d={} {}\n".format(i, j, d, present))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    opts, args = getopt.getopt(argv[1:], "hp:t:l:", ["help", \
                         "problem", "train", "limit"])

    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        limit = 0
        if option in ("-l", "--limit"):
            limit = int(value)
        if option in ("-t", "--train", "-p", "--problem"):
            with open(value) as fileobj:
                file_as_list = list(fileobj)
    if limit:
        file_as_list = file_as_list[:limit]

    for option, value in opts:
        #base_clauses = sudoku_clauses()
        base_clauses = extended_sudoku_clauses()
        #base_clauses = minimal_sudoku_clauses()
        if option in ("-t", "--train"):
            train_list, test_list = split_list(file_as_list)
            before_test_list, after_test_list = split_list(test_list)

            #Before Training:
            #################
            #iterate over the first quarter of sudoku problems to test the performance before
            #training with reduntant clauses
            print("Before Training:")
            process_sudokus(before_test_list, base_clauses)

            #Training:
            #################
            #iterate over the half of sudoku problems to train the SAT solver with
            #reduntant clauses
            print("Training:")
            learnt_clauses = process_sudokus(train_list, base_clauses)
            valid_clauses = check_validity(learnt_clauses, base_clauses)
            write_out_valid_clauses(valid_clauses)

            #After Training:
            #################
            #iterate over the last quarter of sudoku problems to test the performance
            #before training with reduntant clauses
            print("After Training:")
            process_sudokus(after_test_list, add_clauses(base_clauses, valid_clauses))

        if option in ("-p", "--problem"):
            #iterate over the set of sudoku problems
            learnt_clauses = process_sudokus(file_as_list, base_clauses)
            valid_clauses = check_validity(learnt_clauses, base_clauses)
            write_out_valid_clauses(valid_clauses)

if __name__ == "__main__":
    sys.exit(main())
