import sudoku_sat_solver

test = [512, 130, 4, 260, 134, 133, 17, 535, 670, 674, 675, 422, 681, 683, 179, 701, 575, 341, 98, 494, 495, -656, 499, 500, 504, 508]
base_clauses = sudoku_sat_solver.minimal_sudoku_clauses()
sudoku_sat_solver.create_base_dimacs(clauses=base_clauses)
valid_clauses = sudoku_sat_solver.essential_check(clause_to_check=test, base_clauses=base_clauses)
for clause in valid_clauses:
    print(clause)
    for variable in clause:
        print(sudoku_sat_solver.v_inv(abs(variable)))
