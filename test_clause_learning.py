from satispy import Variable, Cnf
from satispy.solver import Minisat

p = Variable('p')
q = Variable('q')
r = Variable('r')

exp = Cnf()
exp &= -p | -q
exp &= -q | -r
exp &= r | p
exp &= q | r

solver = Minisat('minisat %s %s > ./out.log')

solution = solver.solve(exp)

if solution.error != False:
    print "Error:"
    print solution.error
elif solution.success:
    print "Found a solution:"
    print p, solution[p]
    print q, solution[q]
    print r, solution[r]
else:
    print "The expression cannot be satisfied"
