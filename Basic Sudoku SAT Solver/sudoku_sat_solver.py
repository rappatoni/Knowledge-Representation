#!/usr/bin/env python
"""
sudoku_sat_solver.py
"""

import sys
import getopt
import fileinput
import pycosat
from pprint import pprint
from math import sqrt


help_message = '''[options]
Options:
    -h --help           This help
    -p --problem file   Problem to be converted to sat.
'''

def v(i, j, d): 
    return 81 * (i - 1) + 9 * (j - 1) + d

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
            clauses = sudoku_clauses()
            geninput(value,clauses)
            sol = set(pycosat.solve(clauses))

            def read_cell(i, j):
            # return the digit of cell i, j according to the solution
                for d in range(1, 10):
                    if v(i, j, d) in sol:
                        return d
            
            rows, columns = 9, 9;
            sol_grid = [[0 for x in range(rows)] for y in range(columns)] 

            for i in range(1, 10):
                for j in range(1, 10):
                    sol_grid[i - 1][j - 1] = read_cell(i, j)

            pprint(sol_grid)


if __name__ == "__main__":
    sys.exit(main())