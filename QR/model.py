from enum import Enum, unique
#from PIL import Image, ImageDraw, ImageFont

class State:

    def __init__(self, number, state):
        self.number = number
        self.state = state

    def print_state(self):
        print("State:{}".format(self.number))
        for i in range(0,len(self.state),2):
            print("{}, {}".format(self.state[i],self.state[i+1]))

#TODO have to implement a tree data structure
class State_Graph:

    def __init__(self,head_node):
        self.head = head_node
        self.number_nodes = 1

    #TODO Traverse all the nodes and print
    def print_graph(self):
        if (self.number_nodes == 1):
            self.head.print_state()

class CausalGraph:

    def __init__(self, entities, relationships):
        # list of Entity
        self.entities = entities
        # list of relationships
        self.relationships = relationships

    #def draw_graph(self, state):
    '''def draw_graph(self):
        """

        :return: A graphical representation of the current state.
        """
        #I'm assuming we draw just the present state here. We have to concatenate it to the graph of the already
        #given history at a later point when we have all the possible branchings from the past state. I don't
        #think we need the argument state - the CausalGraph should have all information needed in its entities right?
        #So I removed it for now.
        image = Image.new("RGB", (100, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle(((0, 00), (100, 100)), fill="white", outline="green")
        coordinates = (10, 10)
        for entity in self.entities:
            draw.text(coordinates, str(entity.name)+" "+str(entity.current_magnitude), fill="black")
            coordinates+=(0,20)
        image.save("output.jpg", "JPEG")
        return image'''

    # we traverse the causal graph and apply relationships and return a list of next states
    def traverse_graph(self, initial_state):

        current_state = initial_state

        for i in range(0,len(initial_state),2):
            for j in range(0,len(self.entities)):
                for k in range(0,len(self.entities[j].quantities)):
                    self.entities[j].quantities[k].current_magnitude = initial_state[i]
                    self.entities[j].quantities[k].current_derivative = initial_state[i+1]

        init_state = State(0, current_state)
        state_graph = State_Graph(init_state)
        state_graph.print_graph()

        # inequality comparison not supported error
        '''self.relationships[0].apply_relationship()
        self.relationships[1].apply_relationship()
        self.relationships[2].apply_relationship()

        for i in range(0,len(initial_state),2):
            for j in range(0,len(self.entities)):
                for k in range(0,len(self.entities[j].quantities)):
                    current_state[i] = self.entities[j].quantities[k].current_magnitude
                    current_state[i+1] = self.entities[j].quantities[k].current_derivative

        next_state = State(0, current_state)
        next_state.print_state()'''



class Relationship(object):
    def __init__(self, name, causal_party, receiving_party):
        self.name = name
        self.causal_party = causal_party
        self.receiving_party = receiving_party

    def apply_relationship(self):
        # should be implemented by children
        pass

class InfluenceRelationship(Relationship):
    def __init__(self, name, causal_party, receiving_party, sign):
        super(InfluenceRelationship, self).__init__(name, causal_party, receiving_party)
        self.sign = sign

    def apply_relationship(self):
        # TODO add checks for already applied change and
        old_value = self.receiving_party.current_derivative
        new_value = None
        causal_value = self.causal_party.current_magnitude
        if causal_value > QuantitySpace.ZERO:
            if self.sign == QuantitySpace.POSITIVE:
                # I+ and source +
                new_value = self.receiving_party.increase_derivative()
            else:
                # I+ and source -
                new_value = self.receiving_party.decrease_derivative()
        elif causal_value == QuantitySpace.ZERO:
            # if there is no influence, we don't change anything
            new_value = old_value
        else:
            if self.sign == QuantitySpace.POSITIVE:
                # I- and source +
                new_value = self.receiving_party.decrease_derivative()
            else:
                # I- and source -
                new_value = self.receiving_party.increase_derivative()
        return new_value


class ProportionalRelationship(Relationship):
    def __init__(self, name, causal_party, receiving_party, sign):
        super(ProportionalRelationship, self).__init__(name, causal_party, receiving_party)
        self.sign = sign

    def apply_relationship(self):
        # TODO add checks for already applied change and
        old_value = self.receiving_party.current_derivative
        new_value = None
        causal_value = self.causal_party.current_derivative
        if causal_value > Derivative.ZERO:
            if self.sign == Derivative.POSITIVE:
                # P+ and source +
                new_value = self.receiving_party.increase_derivative()
            else:
                # P+ and source -
                new_value = self.receiving_party.decrease_derivative()
        elif causal_value == Derivative.ZERO:
            # there is a proportional influence of 0, we get the receiver to zero
            if self.receiving_party.current_derivative > causal_value:
                new_value = self.receiving_party.decrease_derivative()
            elif self.receiving_party.current_derivative == causal_value:
                new_value = old_value
            else:
                new_value = self.receiving_party.increase_derivative()
        else:
            if self.sign == Derivative.POSITIVE:
                # P- and source +
                new_value = self.receiving_party.decrease_derivative()
            else:
                # P- and source -
                new_value = self.receiving_party.increase_derivative()
        return new_value


@unique
class Variables(Enum):
    def increase(self, comparison_group):
        new_value = self.value + 1
        for single_quantity in comparison_group:
            if single_quantity.value == new_value:
                return True, single_quantity
        return False, self

    def decrease(self, comparison_group):
        new_value = self.value - 1
        for single_quantity in comparison_group:
            if single_quantity.value == new_value:
                return True, single_quantity
        return False, self


class QuantitySpace(Variables):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1
    MAX = 2

    def increase(self, comparison_group):
        super(QuantitySpace,self).increase()

    def decrease(self, comparison_group):
        super(QuantitySpace,self).decrease()


class Derivative(Variables):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1

    def increase(self, comparison_group):
        super(Derivative,self).increase()

    def decrease(self, comparison_group):
        super(Derivative,self).decrease()


class Quantity():
    def __init__(self, name, quantities):
        self.name = name
        self.quantities = quantities
        self.current_magnitude = QuantitySpace.ZERO
        self.current_derivative = Derivative.ZERO
        # a set of qualitative quantities
        # Am I correct in assuming that quantities= comparison group = quantity space (in Dynalearn)?
        # If so, should we not add an attribute quantity? An entity can have multiple quanitities, each with its own
        # quantity space and current magnitude. This isn't a necessary functionality now but will be needed for
        # the "extra" stuff.

    # TODO feasibility check whether moving from one state to another is possible
    # TODO if a derivative changes twice in a loop, we want to know that but implement checking elsewhere
    def increase_derivative(self):
        self.current_derivative = Derivative.increase(self.current_derivative, self.quantities)
        return self.current_derivative

    def decrease_derivative(self):
        self.current_derivative = Derivative.decrease(self.current_derivative, self.quantities)
        return self.current_derivative

    def increase_magnitude(self):
        self.current_magnitude = QuantitySpace.increase(self.current_magnitude, self.quantities)
        return self.current_magnitude

    def decrease_magnitude(self):
        self.current_magnitude = QuantitySpace.decrease(self.current_magnitude, self.quantities)
        return self.current_magnitude

    def apply_derivative(self):
        if self.current_derivative >= Derivative.POSITIVE:
            return self.increase_magnitude
        elif self.current_derivative == Derivative.ZERO:
            return self.current_magnitude
        else:
            return self.decrease_magnitude

    def __str__(self):
        return "name={}, current_magnitude={}, current_derivative={}".format(self.name, self.current_magnitude,
                                                                             self.current_derivative)

class Entity:

    def __init__(self,name):
        self.name = name
        self.quantities = []

    def add_quantity(self, name, quantities):
        self.quantities.append(Quantity(name,quantities))

