#!/usr/bin/env python
"""
sudoku_sat_solver.py
"""

import sys
import getopt
import fileinput
from pprint import pprint
from math import sqrt
from subprocess import call

COMMAND = 'minisat %s %s > %s'
LOGFILE = "minisat.log"
DIMACS_OUT = "dimacs_clauses.txt"
MINISAT_OUT = "minisat_out.txt"

help_message = '''[options]
Options:
    -h --help           This help
    -p --problem file   Problem to be converted to sat.
'''

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
def sudoku_clauses():
    res = []
    # for all cells, ensure that the each cell:
    for i in range(1, 10):
        for j in range(1, 10):
            # denotes (at least) one of the 9 digits (1 clause)
            res.append([v(i, j, d) for d in range(1, 10)])
            # does not denote two different digits at once (36 clauses)
            for d in range(1, 10):
                for dp in range(d + 1, 10):
                    res.append([-v(i, j, d), -v(i, j, dp)])

    def valid(cells):
        for i, xi in enumerate(cells):
            for j, xj in enumerate(cells):
                if i < j:
                    for d in range(1, 10):
                        res.append([-v(xi[0], xi[1], d), -v(xj[0], xj[1], d)])

    # ensure rows and columns have distinct values
    for i in range(1, 10):
        valid([(i, j) for j in range(1, 10)])
        valid([(j, i) for j in range(1, 10)])

    # ensure 3x3 sub-grids "regions" have distinct values
    for i in 1, 4, 7:
        for j in 1, 4 ,7:
            valid([(i + k % 3, j + k // 3) for k in range(9)])

    assert len(res) == 81 * (1 + 36) + 27 * 324
    return res

def extended_sudoku_clauses(): #extended encoding
    res = []
    # for all cells, ensure that the each cell:
    for i in range(1, 10):
        for j in range(1, 10):
            # denotes (at least) one of the 9 digits (1 clause)
            res.append([v(i, j, d) for d in range(1, 10)])
            # does not denote two different digits at once (36 clauses)
            for d in range(1, 10):
                for dp in range(d + 1, 10):
                    res.append([-v(i, j, d), -v(i, j, dp)])

    def valid(cells):
        for i, xi in enumerate(cells):
            for j, xj in enumerate(cells):
                if i < j:
                    for d in range(1, 10):
                        res.append([-v(xi[0], xi[1], d), -v(xj[0], xj[1], d)])

    # ensure rows and columns have distinct values (alldifferent constraints)
    #(2*9*9*9C2 clauses)
    # + redundant constraint: ensure each value appears at least once per columns/row
    # (2*9*9 clauses)
    for i in range(1, 10):
        valid([(i, j) for j in range(1, 10)])
        for d in range (1,10):
            res.append([v(i, j, d) for j in range(1, 10)])
        valid([(j, i) for j in range(1, 10)])
        for d in range(1,10):
            res.append([v(j, i, d) for j in range(1, 10)])


    # ensure 3x3 sub-grids "regions" have distinct values (alldifferent)
    # (9*9*9C2 clauses)
    # +redundant constraint: each value appears at least once per 3x3 box
    #(9*9 clauses)
    for i in 1, 4, 7:
        for j in 1, 4 ,7:
            valid([(i + k % 3, j + k // 3) for k in range(9)])
            for d in range (1,10):
                res.append([v(i+k%3, j+k//3, d) for k in range(9)])

    assert len(res) == 81*(1+36)+ 27 * 324+ 3 * 81
    return res

def minimal_sudoku_clauses(): #minimal Sukoku Encoding
    res = []
    # for all cells, ensure that the each cell:
    for i in range(1, 10):
        for j in range(1, 10):
            # denotes (at least) one of the 9 digits (1 clause)
            res.append([v(i, j, d) for d in range(1, 10)])

    def valid(cells):
        for i, xi in enumerate(cells):
            for j, xj in enumerate(cells):
                if i < j:
                    for d in range(1, 10):
                        res.append([-v(xi[0], xi[1], d), -v(xj[0], xj[1], d)])

    # ensure rows and columns have distinct values (alldifferent constraints)
    #(2*9*9*9C2 clauses)
    for i in range(1, 10):
        valid([(i, j) for j in range(1, 10)])
        valid([(j, i) for j in range(1, 10)])

    # ensure 3x3 sub-grids "regions" have distinct values (alldifferent)
    #(9*9*9C2 clauses)
    for i in 1, 4, 7:
        for j in 1, 4 ,7:
            valid([(i + k % 3, j + k // 3) for k in range(9)])

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
        if j > 9:
            i = i + 1
            j = 1
        if d:
            instance_clauses.append([v(i, j, d)])
        j = j + 1

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
    learnt = []
    with open(logfile, "r") as out_file:
        for line in out_file:
            if line == "clause_found\n":
                clause = next(out_file).strip()
                clause = clause.replace(" 0", "")
                learnt.append(clause)
    return sat, solution, learnt

def add_clauses(base, extra_clauses):
    new_clauses = base[:]
    for clause in extra_clauses:
        new_clauses.append([clause])
    return new_clauses

def negate(clause):
    return [-int(x) for x in clause.strip().split()]

def check_validity(learnt, base_clauses):
    for learn in learnt:
        # for each learnt clause we are interested in if it is a globally valid clause.
        negated_clause = negate(learn)
        instance_clauses = add_clauses(base_clauses, negated_clause)
        dimacs_out(DIMACS_OUT, instance_clauses)
        ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
        satisfied, solution, learnt_clauses = read_results(ret, MINISAT_OUT, LOGFILE)
        # if we found a clause which is not satisfiable - Success!
        if not satisfied:
            print("Success! Globally valid clause={}".format(learn))
            for variable in learn.split():
                i, j, d = v_inv(abs(int(variable)))
                print("i={}, j={}, d={} ".format(i, j, d))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    opts, args = getopt.getopt(argv[1:], "hp:", ["help", \
                         "problem"])

    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-p", "--problem"):
            #base_clauses = sudoku_clauses()
            #base_clauses = extended_sudoku_clauses()
            base_clauses = minimal_sudoku_clauses()
            with open(value) as fileobj:
                file_as_list = list(fileobj)
                #iterate over the set of sudoku problems
                for index, sudoku in enumerate(file_as_list):
                    print("{} of {}".format(index + 1, len(file_as_list)))
                    instance_clauses = read_sudoku(sudoku, base_clauses)

                    #solve using MiniSAT
                    dimacs_out(DIMACS_OUT, instance_clauses)
                    ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
                    satisfied, solution, learnt = read_results(ret, MINISAT_OUT, LOGFILE)
                    if not satisfied:
                        print("UNSAT!")
                        #for variable in solution:
                            #i, j, d = v_inv(abs(variable))
                            #print("variable={}, i={}, j={}, d={}".format(abs(variable), i, j, d))
                    if learnt:
                        print("clauses learnt={}".format(len(learnt)))
                        check_validity(learnt, base_clauses)

if __name__ == "__main__":
    sys.exit(main())
