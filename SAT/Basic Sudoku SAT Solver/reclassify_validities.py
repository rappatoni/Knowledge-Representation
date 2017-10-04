import sudoku_sat_solver

def read_validities(filename):
    validities = set()
    with open(filename) as fileobj:
        lines = fileobj.readlines()
        for line in lines:
            validities.add(frozenset([int(x) for x in line.strip().split()]))
    return validities

def classify_validities(base_clauses_with_cats, valid_clauses):
    cats = ["vcell", "ucell", "vrow", "urow", "vcol", "ucol", "vblock", "ublock", "new"]
    valid_dict = {cat: set() for cat in cats}
    # Comparing valid clauses and base clauses
    for clause in valid_clauses:
        is_new_type = True
        for key in base_clauses_with_cats:
            for baseclause in base_clauses_with_cats[key]:
                if baseclause == clause:
                    valid_dict[key].add(clause)
                    is_new_type = False
        if is_new_type:
            valid_dict["new"].add(clause)
    return valid_dict

validities = read_validities("10000_15000_extended_batch_size_50_validities.txt")
base_clauses_with_cats = sudoku_sat_solver.extended_sudoku_clauses_with_cats()
classified_validities = classify_validities(base_clauses_with_cats, validities)
for key in classified_validities:
    print("key={}, len={}".format(key, len(classified_validities[key])))
    if key == "new" and len(classified_validities[key]) > 0:
        for clause in classified_validities[key]:
            print(clause)
            for variable in clause:
                print(sudoku_sat_solver.v_inv(abs(variable)))
