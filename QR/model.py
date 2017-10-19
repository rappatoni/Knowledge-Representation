from enum import Enum, unique
from typing import Dict, List, Union, Tuple, Optional
#from PIL import Image, ImageDraw, ImageFont
class Variable(Enum):
    def increase(self, comparison_group: List['Variable']) -> Tuple[bool, 'Variable']:
        new_value = self.value + 1
        for single_quantity in comparison_group:
            if single_quantity.value == new_value:
                return True, single_quantity
        return False, self

    def decrease(self, comparison_group: List['Variable']) -> Tuple[bool, 'Variable']:
        new_value = self.value - 1
        for single_quantity in comparison_group:
            if single_quantity.value == new_value:
                return True, single_quantity
        return False, self

    def __lt__(self, other: 'Variable') -> bool:
        return self.value < other.value

    def ___le__(self, other: 'Variable') -> bool:
        return self.value <= other.value

    def __eq__(self, other: 'Variable') -> bool:
        return self.value == other.value

    def __ne__(self, other: 'Variable') -> bool:
        return self.value != other.value

    def __gt__(self, other: 'Variable') -> bool:
        return self.value > other.value

    def __ge__(self, other: 'Variable') -> bool:
        return self.value >= other.value

class QuantityValue(Variable):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1
    MAX = 2

    def increase(self, comparison_group: List[Variable]) -> Tuple[bool, Variable]:
        return super(QuantityValue, self).increase(comparison_group)

    def decrease(self, comparison_group: List[Variable]) -> Tuple[bool, Variable]:
        return super(QuantityValue, self).decrease(comparison_group)


class Derivative(Variable):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1

    def increase(self, comparison_group: List[Variable]) -> Tuple[bool, Variable]:
        return super(Derivative, self).increase(comparison_group)

    def decrease(self, comparison_group: List[Variable]) -> Tuple[bool, Variable]:
        return super(Derivative, self).decrease(comparison_group)


class Quantity:
    def __init__(self, name: str, quantity_space: List[QuantityValue]) -> None:
        self.name = name
        # a set of qualitative quantity_space
        # TODO change to dict in order to support multiple quantities per entity.
        self.quantity_space: List[QuantityValue] = quantity_space
        self.current_magnitude: QuantityValue = QuantityValue.ZERO
        self.current_derivative: Derivative = Derivative.ZERO

    # TODO feasibility check whether moving from one state to another is possible
    # TODO if a derivative changes twice in a loop, we want to know that but implement checking elsewhere
    def increase_derivative(self) -> Tuple[bool, Derivative]:
        changed, self.current_derivative = self.current_derivative.increase(Derivative)
        return changed, self.current_derivative

    def decrease_derivative(self) -> Tuple[bool, Derivative]:
        changed, self.current_derivative = self.current_derivative.decrease(Derivative)
        return changed, self.current_derivative

    def increase_magnitude(self) -> Tuple[bool, QuantityValue]:
        changed, self.current_magnitude = self.current_magnitude.increase(self.quantity_space)
        return changed, self.current_magnitude

    def decrease_magnitude(self) -> Tuple[bool, QuantityValue]:
        changed, self.current_magnitude = self.current_magnitude.decrease(self.quantity_space)
        return changed, self.current_magnitude

    def apply_derivative(self) -> bool:
        if self.current_derivative > Derivative.ZERO:
            return self.increase_magnitude()[0]
        elif self.current_derivative == Derivative.ZERO:
            return False
        else:
            return self.decrease_magnitude()[0]

    def __str__(self) -> str:
        return "name={}, current_magnitude={}, current_derivative={}".format(self.name, self.current_magnitude,
                                                                             self.current_derivative)

class Entity:

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.quantities: List[Quantity] = []

    def add_quantity(self, quantity: Quantity) -> None:
        self.quantities.append(quantity)

class Relationship(object):
    def __init__(self, name: str, causal_party: Quantity, receiving_party: Quantity) -> None:
        self.name = name
        self.causal_party = causal_party
        self.receiving_party = receiving_party

    def apply_relationship(self) -> bool:
        # should be implemented by children
        pass

class InfluenceRelationship(Relationship):
    def __init__(self, name: str, causal_party: Quantity, receiving_party: Quantity, sign: Derivative) -> None:
        super(InfluenceRelationship, self).__init__(name, causal_party, receiving_party)
        self.sign = sign

    def apply_relationship(self) -> bool:
        causal_value = self.causal_party.current_magnitude
        changed = False
        if causal_value > QuantityValue.ZERO:
            if self.sign == Derivative.POSITIVE:
                # I+ and source +
                changed, new_value = self.receiving_party.increase_derivative()
            else:
                # I+ and source -
                changed, new_value = self.receiving_party.decrease_derivative()
        elif causal_value == QuantityValue.ZERO:
            # if there is no influence, we change the derivate to zero
            if self.receiving_party.current_derivative != Derivative.ZERO:
                changed = True
            self.receiving_party.current_derivative = Derivative.ZERO
            new_value = Derivative.ZERO
        else:
            if self.sign == Derivative.POSITIVE:
                # I- and source +
                changed, new_value = self.receiving_party.decrease_derivative()
            else:
                # I- and source -
                changed, new_value = self.receiving_party.increase_derivative()
        return changed


class ProportionalRelationship(Relationship):
    def __init__(self, name: str, causal_party: Quantity, receiving_party: Quantity, sign: Derivative) -> None:
        super(ProportionalRelationship, self).__init__(name, causal_party, receiving_party)
        self.sign = sign

    def apply_relationship(self) -> bool:
        # TODO add checks for already applied change and
        changed = False
        causal_value = self.causal_party.current_derivative
        if causal_value > Derivative.ZERO:
            if self.sign == Derivative.POSITIVE:
                # P+ and source +
                changed, new_value = self.receiving_party.increase_derivative()
            else:
                # P+ and source -
                changed, new_value = self.receiving_party.decrease_derivative()
        elif causal_value == Derivative.ZERO:
            # there is a proportional influence of 0, we get the receiver to zero
            if self.receiving_party.current_derivative > causal_value:
                changed, new_value = self.receiving_party.decrease_derivative()
            elif self.receiving_party.current_derivative < causal_value:
                changed, new_value = self.receiving_party.increase_derivative()
            # else we do nothing
        else:
            if self.sign == Derivative.POSITIVE:
                # P- and source +
                changed, new_value = self.receiving_party.decrease_derivative()
            else:
                # P- and source -
                changed, new_value = self.receiving_party.increase_derivative()
        return changed
# Type definition
State = List[Union[QuantityValue,Derivative]]

class CausalGraph:
    def __init__(self, entities: List[Entity], relationships: List[Relationship]) -> None:
        # list of Entity
        self.entities: List[Entity] = entities
        # list of relationships
        self.relationships: List[Relationship] = relationships

    #def draw_graph(self, state):
    '''def draw_graph(self) -> None:
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
    def apply_state(self, state_values: State) -> None:
        counter = 0
        for j in range(0, len(self.entities)):
            for k in range(0, len(self.entities[j].quantities)):
                self.entities[j].quantities[k].current_magnitude = state_values[j*2 + k]
                self.entities[j].quantities[k].current_derivative = state_values[j*2 + k + 1]

    def record_state(self) -> State:
        state_values: State = list()
        for j in range(0, len(self.entities)):
            for k in range(0,len(self.entities[j].quantities)):
                state_values.append(self.entities[j].quantities[k].current_magnitude)
                state_values.append(self.entities[j].quantities[k].current_derivative)
        return state_values

    def apply_point_changes(self) -> Tuple[bool, State]:
        # Here we apply changes from 0 to something
        changed = False
        # start with applying derivative
        for j in range(0, len(self.entities)):
            for k in range(0,len(self.entities[j].quantities)):
                if self.entities[j].quantities[k].current_magnitude == QuantityValue.ZERO:
                    # if the quantity is zero and the derivative is not zero
                    if self.entities[j].quantities[k].current_derivative != Derivative.ZERO:
                        changed |= self.entities[j].quantities[k].apply_derivative()
        # then we apply potential influence changes which could be pending
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship and relationship.receiving_party.current_derivative == Derivative.ZERO:
                changed |= relationship.apply_relationship()
        return changed, self.record_state()

    def apply_static_changes(self) -> Tuple[bool, State]:
        # Here we apply ProportionalRelationship + EquivalenceRelationship
        changed = False
        for relationship in self.relationships:
            if type(relationship) == ProportionalRelationship:
                changed |= relationship.apply_relationship()
        return changed, self.record_state()

    def apply_interval_changes(self, initial_state: State) -> Tuple[bool, List[State]]:
        # Here we apply InfluenceRelationship + Derivative
        changes = list()
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship:
                changed = relationship.apply_relationship()
                if changed:
                    changes.append(self.record_state())
                # we go back to the original state
                self.apply_state(initial_state)
        for entity in self.entities:
            for quantity in entity.quantities:
                changed = quantity.apply_derivative()
                if changed:
                    changes.append(self.record_state())
                # we go back to the original state
                self.apply_state(initial_state)
        return len(changes) != 0, changes

    def compute_next_states(self, initial_state: State) -> List[State]:
        self.apply_state(initial_state)
        changed, new_state_values = self.apply_point_changes()
        if changed:
            changed, new_state_values = self.apply_static_changes()
            return [new_state_values]
        next_states = list()
        changed, new_states = self.apply_interval_changes(initial_state)
        for state in new_states:
            self.apply_state(state)
            self.apply_static_changes()
            next_states.append(self.record_state())
        return next_states

    def __str__(self) -> str:
        value = ""
        for j in range(0, len(self.entities)):
            value += self.entities[j].name + "\n"
            for k in range(0,len(self.entities[j].quantities)):
                value += "\t{}\n".format(self.entities[j].quantities[k].name)
                value += "\t\tm={}, d={}\n".format(
                      self.entities[j].quantities[k].current_magnitude,
                      self.entities[j].quantities[k].current_derivative)
        return value

class StateNode(object):

    #type: ignore
    def __init__(self, parent: Optional['StateNode'], number: int, state_values: State) -> None:
        self.parent = parent
        self.children: List['StateNode'] = list()
        self.number = number
        self.state_values: State = state_values[:]

    def add_child(self, child: 'StateNode') -> None:
        self.children.append(child)

    def print_state(self) -> None:
        print("State:{}".format(self.number))
        for i in range(0,len(self.state_values),2):
            print("{}, {}".format(self.state_values[i],self.state_values[i+1]))

    def __str__(self) -> str:
        value = ""
        parent_number = 0
        if self.parent:
            parent_number = self.parent.number
        value += "{}: (parent={})\n".format(self.number, parent_number)
        for i in range(0, len(self.state_values), 2):
            value += "    m={}, d={}\n".format(self.state_values[i], self.state_values[i+1])
        for child in self.children:
            value += "    c={}".format(child.number)
        return value

#TODO have to implement a tree data structure
class State_Graph(object):

    def __init__(self, initial_state: State, causal_graph: CausalGraph) -> None:
        # we count from 1
        self.head: StateNode = StateNode(None, 1, initial_state)
        self.number_nodes: int = 1
        self.states: Dict[str, StateNode] = {"1" : self.head}
        self.causal_graph = causal_graph

    #TODO Traverse all the nodes and print
    def print_graph(self) -> None:
        if (self.number_nodes == 1):
            self.head.print_state()

    def get_next_index(self) -> int:
        self.number_nodes += 1
        return self.number_nodes

    def make_graph(self) -> Dict[str, StateNode]:
        stack = [self.head]
        while len(stack) != 0:
            current_state = stack.pop()
            next_states = self.causal_graph.compute_next_states(current_state.state_values)
            for state in next_states:
                if not self.state_already_exists(state):
                    next_index = self.get_next_index()
                    new_node = StateNode(current_state, next_index, state)
                    stack.append(new_node)
                    self.states[str(next_index)] = new_node
                else:
                    #TODO move the child link of the parent to the one it is a duplicate of
                    pass

        return self.states

    def state_already_exists(self, state: State) -> bool:
        for state_number in self.states:
            state_node = self.states[state_number]
            if state == state_node.state_values:
                return True
        return False

    def __str__(self) -> str:
        value = ""
        for key in self.states:
            value += "{}".format(self.states[key])
        return value
