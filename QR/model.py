import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import random
from enum import Enum, unique
from typing import Dict, List, Union, Tuple, Optional
from collections import defaultdict
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
        self.quantity_space: List[QuantityValue] = quantity_space
        self.current_magnitude: QuantityValue = QuantityValue.ZERO
        self.current_derivative: Derivative = Derivative.ZERO

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
        changed = False
        if self.current_derivative > Derivative.ZERO:
            changed, new_value = self.increase_magnitude()

        elif self.current_derivative < Derivative.ZERO:
            changed, new_value = self.decrease_magnitude()

        if changed:
            print("{} derivate was applied".format(self.name))
        return changed

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
        if changed:
            print("{} was applied".format(self.name))
        return changed


class ProportionalRelationship(Relationship):
    def __init__(self, name: str, causal_party: Quantity, receiving_party: Quantity, sign: Derivative) -> None:
        super(ProportionalRelationship, self).__init__(name, causal_party, receiving_party)
        self.sign = sign

    def apply_relationship(self) -> bool:
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
        if changed:
            print("{} was applied".format(self.name))
        return changed

class EquivalenceRelationship(Relationship):
    def __init__(self, name: str, causal_party: Quantity, receiving_party: Quantity, equivalences: List[QuantityValue]) -> None:
        super(EquivalenceRelationship, self).__init__(name, causal_party, receiving_party)
        self.equivalences = equivalences

    def apply_relationship(self) -> bool:
        changed = False
        # a causal value is the value in the equivalence relationship which needs to be equivalent.
        for causal_value in self.equivalences:
            if self.causal_party.current_magnitude == causal_value:
                if self.receiving_party.current_magnitude != causal_value:
                    self.receiving_party.current_magnitude = causal_value
                    changed = True
        for causal_value in self.equivalences:
            if self.receiving_party.current_magnitude == causal_value:
                if self.causal_party.current_magnitude != causal_value:
                    self.causal_party.current_magnitude = causal_value
                    changed = True
        if changed:
            print("{} was applied".format(self.name))
        return changed
# Type definition
State = List[Union[QuantityValue,Derivative]]

class CausalGraph:
    def __init__(self, entities: List[Entity], relationships: List[Relationship]) -> None:
        # list of Entity
        self.entities: List[Entity] = entities
        # list of relationships
        self.relationships: List[Relationship] = relationships

    # we traverse the causal graph and apply relationships and return a list of next states
    def apply_state(self, state_values: State) -> None:
        counter = 0
        for e_index, entity in enumerate(self.entities):
            for q_index, quantity in enumerate(entity.quantities):
                quantity.current_magnitude = state_values[counter]
                quantity.current_derivative = state_values[counter + 1]
                counter += 2

    def record_state(self) -> State:
        state_values: State = list()
        for e_index, entity in enumerate(self.entities):
            for q_index, quantity in enumerate(entity.quantities):
                state_values.append(quantity.current_magnitude)
                state_values.append(quantity.current_derivative)
        return state_values

    def apply_point_changes(self, initial_state: State) -> Tuple[bool, State]:
        # Here we apply changes from 0 to something
        changed = False
        # start with applying derivative
        for e_index, entity in enumerate(self.entities):
            for q_index, quantity in enumerate(entity.quantities):
                if quantity.current_derivative != Derivative.ZERO:

                    if quantity.current_magnitude == QuantityValue.ZERO:
                        changed |= quantity.apply_derivative()
                    if quantity.current_magnitude == QuantityValue.MAX:
                        changed |= quantity.apply_derivative()

        # then we apply potential influence changes which could be pending
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship and relationship.receiving_party.current_derivative == Derivative.ZERO:
                changed |= relationship.apply_relationship()
        # we go back to the original state
        return_state = self.record_state()
        self.apply_state(initial_state)
        return changed, return_state

    def apply_static_changes(self, initial_state: State) -> Tuple[bool, State]:
        # Here we apply ProportionalRelationship + EquivalenceRelationship
        changed = False
        this_round_changed = True
        while this_round_changed:
            this_round_changed = False
            for relationship in self.relationships:
                if type(relationship) == ProportionalRelationship:
                    this_round_changed |= relationship.apply_relationship()
                if type(relationship) == EquivalenceRelationship:
                    this_round_changed |= relationship.apply_relationship()
            changed |= this_round_changed
        # we go back to the original state
        return_state = self.record_state()
        self.apply_state(initial_state)
        return changed, return_state

    def apply_interval_changes(self, initial_state: State) -> Tuple[bool, List[State]]:
        # Here we apply InfluenceRelationship + Derivative
        changes = list()
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship:
                changed = relationship.apply_relationship()
                if changed:
                    print("Possible branch")
                    changes.append(self.record_state())
                # we go back to the original state
                self.apply_state(initial_state)
        for entity in self.entities:
            for quantity in entity.quantities:
                changed = quantity.apply_derivative()
                if changed:
                    print("Possible branch")
                    changes.append(self.record_state())
                # we go back to the original state
                self.apply_state(initial_state)
        changed, state = self.apply_exo_decrease(initial_state)
        if changed:
            print("Possible branch")
            changes.append(state)
            self.apply_state(initial_state)
        return len(changes) != 0, changes

    def apply_exo_decrease(self, initial_state: State) -> Tuple[bool, State]:
        # we know where it is...
        changed, _ = self.entities[0].quantities[0].decrease_derivative()
        if changed:
             print("2nd order derivative applied")
        # we go back to the original state
        return_state = self.record_state()
        self.apply_state(initial_state)
        return changed, return_state

    def am_consistent(self, old_state: State) -> bool:
        counter = 0
        for e_index, entity in enumerate(self.entities):
            for q_index, quantity in enumerate(entity.quantities):
                # if the quantity increased the derivative better be positive
                if quantity.current_magnitude > old_state[counter]:
                     if quantity.current_derivative <= Derivative.ZERO:
                         reason = "Illegal state thrown away. {} magnitude's increased but derivative was <= 0".format(quantity.name)
                         return False, reason
                # if the quantity decreased the derivative better be negative
                if quantity.current_magnitude < old_state[counter]:
                     if quantity.current_derivative >= Derivative.ZERO:
                         reason = "Illegal state thrown away. {} magnitude's decreased but derivative was >= 0".format(quantity.name)
                         return False, reason
                counter += 2

        influences: Dict[str, List[InfluenceRelationship]] = defaultdict(lambda: list())
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship:
                influences[relationship.receiving_party.name].append(relationship)
        for key in influences:
            # we only check if there are two, we don't check if they are +/-
            if len(influences[key]) >= 2:
                positive_causal_party = None
                negative_causal_party = None
                victim = None
                for relationship in influences[key]:
                    victim = relationship.receiving_party
                    if relationship.sign == Derivative.POSITIVE:
                        positive_causal_party = relationship.causal_party
                    if relationship.sign == Derivative.NEGATIVE:
                        negative_causal_party = relationship.causal_party

                if positive_causal_party.current_magnitude != QuantityValue.ZERO and negative_causal_party.current_magnitude != QuantityValue.ZERO and positive_causal_party.current_derivative != negative_causal_party.current_derivative:
                    if victim.current_derivative == Derivative.ZERO:
                        reason = "Illegal state thrown away. I+(A,B) and I-(C,B) and delta A  != delta C then delta B != 0".format()
                        return False, reason
        return True, ""

    def compute_next_states(self, initial_state: State) -> List[State]:
        self.apply_state(initial_state)
        changed, new_state_values = self.apply_point_changes(initial_state)
        if changed:
            self.apply_state(new_state_values)
            changed, new_state_values = self.apply_static_changes(new_state_values)
            return [new_state_values]
        next_states = list()
        changed, new_states = self.apply_interval_changes(initial_state)
        if len(new_states) == 0:
            print("No changes")
        for state in new_states:
            self.apply_state(state)
            changed, new_state_values = self.apply_static_changes(state)
            self.apply_state(new_state_values)
            is_consistent, reason = self.am_consistent(initial_state)
            if is_consistent:
                next_states.append(new_state_values)
            else:
                self.print_illegal_state(new_state_values, reason)
        return next_states

    def print_illegal_state(self, new_state_values: State, reason: str) -> None:
        print("  *************** Inconsistent state ***************")
        print("  Reason:  {}".format(reason))
        StateNode.print_state(new_state_values)
        print("             ******************************")

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

    def add_child(self, new_child: 'StateNode') -> None:
        for child in self.children:
            # we don't want to add duplicates of children
            if child.number == new_child.number:
                return
        self.children.append(new_child)

    @staticmethod
    def print_state(state: State) -> None:
        for i in range(0,len(state),2):
            print("{}, {}".format(state[i], state[i+1]))

    def __str__(self) -> str:
        value = ""
        parent_number = 0
        if self.parent:
            parent_number = self.parent.number
        value += "{}: (parent={})\n".format(self.number, parent_number)
        for i in range(0, len(self.state_values), 2):
            value += "    m={}, d={}\n".format(self.state_values[i], self.state_values[i+1])
        for child in self.children:
            value += "    c={}\n".format(child.number)
        return value

    '''def draw_node(self) -> None:
        """
        :return: A graphical representation of the current state.
        """
        # I'm assuming we draw just the present state here. We have to concatenate it to the graph of the already
        # given history at a later point when we have all the possible branchings from the past state. I don't
        # think we need the argument state - the CausalGraph should have all information needed in its entities right?
        # So I removed it for now.
        image = Image.new("RGB", (100, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle(((0, 00), (100, 100)), fill="white", outline="green")
        coordinates = (10, 10)
        #for node in self.entities:
            draw.text(coordinates, str(self.state_values) + " " + str(self.current_magnitude), fill="black")
            coordinates += (0, 20)
        image.save("output.jpg", "JPEG")
        return image'''

class State_Graph(object):

    def __init__(self, initial_state: State, causal_graph: CausalGraph) -> None:
        # we count from 1
        self.head: StateNode = StateNode(None, 1, initial_state)
        self.number_nodes: int = 1
        self.states: Dict[str, StateNode] = {"1" : self.head}
        self.causal_graph = causal_graph

    #TODO Traverse all the nodes and print
    def print_graph(self, states) -> None:
        G = nx.DiGraph()
        get_edges=[]
        get_nodes={}
        for key in states:
            for child in states[key].children:
                get_edges+=[(states[key].number, child.number)]
            get_nodes[int(key)]=[states[key].number]
        G.add_edges_from(get_edges)

        #Fix initial node positions for better graphs
        initial_node_positions={}
        for node in get_nodes:
            if node==1:
                initial_node_positions[1]=(0,0)
            else:
                initial_node_positions[node] = ((np.random.uniform(100*(node-1), 100*node)), np.random.uniform(100*(node-1), 100*node))

        fixed_nodes=[1]

        pos = nx.spring_layout(G, pos=initial_node_positions, fixed=fixed_nodes)
        nodes=nx.draw_networkx_nodes(G, pos, node_color="white", linewidths= 1.0, node_size=1000)
        nodes.set_edgecolor('black')
        nx.draw_networkx_labels(G, pos)
        nx.draw_networkx_edges(G, pos, arrows=True)
        plt.show()

    def get_next_index(self) -> int:
        self.number_nodes += 1
        return self.number_nodes

    def make_graph(self) -> Dict[str, StateNode]:
        stack = [self.head]
        while len(stack) != 0:
            current_state = stack.pop()
            print("================= STATE NUMBER: {} =====================".format(current_state.number))
            StateNode.print_state(current_state.state_values)
            print("    ================================================    ".format(current_state.number))
            next_states = self.causal_graph.compute_next_states(current_state.state_values)
            for state in next_states:
                exists, number = self.get_state_number(state)
                if not exists:
                    new_node = StateNode(current_state, number, state)
                    current_state.add_child(new_node)
                    stack.append(new_node)
                    self.states[str(number)] = new_node
                else:
                    current_state.add_child(self.states[str(number)])

        return self.states

    def get_state_number(self, state: State) -> Tuple[bool, int]:
        for state_number in self.states:
            state_node = self.states[state_number]
            if state == state_node.state_values:
                return True, int(state_number)
        return False, self.get_next_index()

    def __str__(self) -> str:
        value = ""
        for key in self.states:
            value += "{}\n".format(self.states[key])
        return value
