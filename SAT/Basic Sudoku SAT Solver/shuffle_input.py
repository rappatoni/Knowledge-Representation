import random
def shuffle_list(input):
    random.shuffle(input)

def read_input(filename):
    with open(filename, "r") as fileobj:
        return list(fileobj)

def write_input(filename, list_of_lines):
    with open(filename, "w+") as fileobj:
        for line in list_of_lines:
            fileobj.write(line)

input_file = read_input("input.txt")
shuffle_list(input_file)
write_input("shuffled_input.txt", input_file)
