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

def geninput(filename,clauses):

    i = 0
    j = 0
    with open(filename) as fileobj:
        while True:
            c = fileobj.read(1)
            if c == "\n":
                break
            d = int(c)
            #print (d)
            if d:
                #print (d)
                #print ("row:{0} column:{1} value:{2}".format(i,j,d))
                clauses.append([v(i, j, d)])
            j = j + 1
            if j > 8:
                i = i + 1
                j = 0

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
                if variable == 0:
                    continue
                solution.append(variable)
    # we extract the learnt clauses
    learnt = []
    with open(logfile, "r") as out_file:
        for line in out_file:
            if line == "clause_found\n":
                clause = next(out_file).strip()
                learnt.append(clause)
    return sat, solution, learnt



def main(argv=None):
    COMMAND = 'minisat %s %s > %s'
    LOGFILE = "minisat.log"
    DIMACS_OUT = "dimacs_clauses.txt"
    MINISAT_OUT = "minisat_out.txt"

    if argv is None:
        argv = sys.argv
    opts, args = getopt.getopt(argv[1:], "hp:", ["help", \
                         "problem"])

    # option processing
    for option, value in opts:
        if option in ("-h", "--help"):
            raise Usage(help_message)
        if option in ("-p", "--problem"):
            clauses = sudoku_clauses()
            geninput(value,clauses)
            dimacs_out(DIMACS_OUT, clauses)
            ret = call(COMMAND % (DIMACS_OUT, MINISAT_OUT, LOGFILE), shell=True)
            satisfied, solution, learnt = read_results(ret, MINISAT_OUT, LOGFILE)
            if satisfied:
                print("SAT")
                for variable in solution:
                    i, j, d = v_inv(abs(variable))
                    #print("variable={}, i={}, j={}, d={}".format(abs(variable), i, j, d))
            if learnt:
                for learn in learnt:
                    print(learn)


if __name__ == "__main__":
    sys.exit(main())
