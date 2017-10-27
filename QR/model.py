import numpy as np
# uncomment this section to generate a graph
#import networkx as nx
#import matplotlib.pyplot as plt
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

    def apply_derivative(self) -> Tuple[bool, str]:
        changed = False
        if self.current_derivative > Derivative.ZERO:
            changed, new_value = self.increase_magnitude()

        elif self.current_derivative < Derivative.ZERO:
            changed, new_value = self.decrease_magnitude()

        reason = ""
        if changed:
            reason = "{} derivate was applied".format(self.name)
        return changed, reason

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
        reason = ""
        if changed:
            reason = "{} was applied".format(self.name)
        return changed, reason


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
        reason = ""
        if changed:
            reason = "{} was applied".format(self.name)
        return changed, reason

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
        reason = ""
        if changed:
            reason = "{} was applied".format(self.name)
        return changed, reason
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

    def apply_point_changes(self, initial_state: State) -> Tuple[bool, State, List[str]]:
        # Here we apply changes from 0 to something
        changed = False
        reasons = list()
        # start with applying derivative
        for e_index, entity in enumerate(self.entities):
            for q_index, quantity in enumerate(entity.quantities):
                if quantity.current_derivative != Derivative.ZERO:

                    if quantity.current_magnitude == QuantityValue.ZERO:
                        change, reason = quantity.apply_derivative()
                        if change:
                            reasons.append(reason)
                            changed = True
                    if quantity.current_magnitude == QuantityValue.MAX:
                        change, reason =quantity.apply_derivative()
                        if change:
                            reasons.append(reason)
                            changed = True

        # then we apply potential influence changes which could be pending
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship and relationship.receiving_party.current_derivative == Derivative.ZERO:
                change, reason = relationship.apply_relationship()
                if change:
                    reasons.append(reason)
                    changed = True
        # we go back to the original state
        return_state = self.record_state()
        self.apply_state(initial_state)
        return changed, return_state, [reason + " - (intra-state change)" for reason in reasons]

    def apply_static_changes(self, initial_state: State) -> Tuple[bool, State, List[str]]:
        # Here we apply ProportionalRelationship + EquivalenceRelationship
        changed = False
        reasons = list()
        this_round_changed = True
        while this_round_changed:
            this_round_changed = False
            for relationship in self.relationships:
                if type(relationship) == ProportionalRelationship:
                    change, reason = relationship.apply_relationship()
                    if change:
                        reasons.append(reason)
                        this_round_changed = True
                        changed = True
                if type(relationship) == EquivalenceRelationship:
                    change, reason = relationship.apply_relationship()
                    if change:
                        reasons.append(reason)
                        this_round_changed = True
                        changed = True
        # we go back to the original state
        return_state = self.record_state()
        self.apply_state(initial_state)
        return changed, return_state, [reason + " - (inter-state change)" for reason in reasons]

    def apply_interval_changes(self, initial_state: State) -> Tuple[bool, List[State], List[str]]:
        # Here we apply InfluenceRelationship + Derivative
        changes = list()
        reasons = list()
        for relationship in self.relationships:
            if type(relationship) == InfluenceRelationship:
                changed, reason = relationship.apply_relationship()
                if changed:
                    reasons.append(reason)
                    changes.append(self.record_state())
                # we go back to the original state
                self.apply_state(initial_state)
        for entity in self.entities:
            for quantity in entity.quantities:
                changed, reason = quantity.apply_derivative()
                if changed:
                    reasons.append(reason)
                    changes.append(self.record_state())
                # we go back to the original state
                self.apply_state(initial_state)
        changed, state = self.apply_exo_decrease(initial_state)
        if changed:
            reason = "2nd order derivative applied"
            reasons.append(reason)
            changes.append(state)
            self.apply_state(initial_state)
        return len(changes) != 0, changes, [reason + " - (intra-state change)" for reason in reasons]

    def apply_exo_decrease(self, initial_state: State) -> Tuple[bool, State]:
        # we know where it is...
        changed, _ = self.entities[0].quantities[0].decrease_derivative()
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

    def compute_next_states(self, initial_state: State) -> Tuple[List[State], List[List[str]]]:
        self.apply_state(initial_state)
        complete_reasons = list()
        changed, new_state_values, reasons = self.apply_point_changes(initial_state)
        if changed:
            complete_reasons += reasons
            self.apply_state(new_state_values)
            changed, new_state_values, reasons = self.apply_static_changes(new_state_values)
            complete_reasons += reasons
            return [new_state_values], [complete_reasons]
        next_states = list()
        changed, new_states, interval_reasons = self.apply_interval_changes(initial_state)
        if len(new_states) == 0:
            print("No changes")
        for state_index, state in enumerate(new_states):
            reason = interval_reasons[state_index]
            self.apply_state(state)
            changed, extra_state_values, extra_reasons = self.apply_static_changes(state)
            self.apply_state(extra_state_values)
            is_consistent, consistency_reason = self.am_consistent(initial_state)
            if is_consistent:
                next_states.append(extra_state_values)
                complete_reasons.append([reason] + extra_reasons)
            else:
                self.print_illegal_state(extra_state_values, consistency_reason, [reason] + extra_reasons)
        return next_states, complete_reasons

    def print_illegal_state(self, new_state_values: State, reason: str, change_reasons: List[str]) -> None:
        print("    ************* Inconsistent state **************")
        for change_reason in change_reasons:
            print("  Attempted change:  {}".format(change_reason))
        print("  Reason:  {}".format(reason))
        StateNode.print_state(new_state_values)
        print("    ******************************")

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
    def __init__(self, parent: Optional['StateNode'], number: int, state_values: State, reasons: List[str]) -> None:
        self.parent = parent
        self.children: List['StateNode'] = list()
        self.number = number
        self.reasons = reasons
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

class State_Graph(object):

    def __init__(self, initial_state: State, causal_graph: CausalGraph) -> None:
        # we count from 1
        self.head: StateNode = StateNode(None, 1, initial_state, [""])
        self.number_nodes: int = 1
        self.states: Dict[str, StateNode] = {"1" : self.head}
        self.causal_graph = causal_graph

# uncomment this section to generate a graph
#    def print_graph(self, states) -> None:
#        G = nx.DiGraph()
#        get_edges=[]
#        get_nodes={}
#        for key in states:
#            for child in states[key].children:
#                get_edges+=[(states[key].number, child.number)]
#            get_nodes[int(key)]=[states[key].number]
#        G.add_edges_from(get_edges)
#
#        #Fix initial node positions for better graphs
#        initial_node_positions={}
#        for node in get_nodes:
#            if node==1:
#                initial_node_positions[1]=(0,0)
#            else:
#                initial_node_positions[node] = ((np.random.uniform(100*(node-1), 100*node)), np.random.uniform(100*(node-1), 100*node))
#
#        fixed_nodes=[1]
#
#        pos = nx.spring_layout(G, pos=initial_node_positions, fixed=fixed_nodes)
#        nodes=nx.draw_networkx_nodes(G, pos, node_color="white", linewidths= 1.0, node_size=1000)
#        nodes.set_edgecolor('black')
#        nx.draw_networkx_labels(G, pos)
#        nx.draw_networkx_edges(G, pos, arrows=True)
#        plt.axis('off')
#        plt.show()

    def get_next_index(self) -> int:
        self.number_nodes += 1
        return self.number_nodes

    def make_graph(self) -> Dict[str, StateNode]:
        stack = [self.head]
        while len(stack) != 0:
            current_state = stack.pop()
            parent_number = 0
            if current_state.parent != None:
                parent_number = current_state.parent.number
            print("============== STATE NUMBER: {} (parent={}) ==============".format(current_state.number, parent_number))
            for reason in current_state.reasons:
                print(reason)
            StateNode.print_state(current_state.state_values)
            next_states, reasons = self.causal_graph.compute_next_states(current_state.state_values)
            for state_index, state in enumerate(next_states):
                exists, number = self.get_state_number(state)
                if not exists:
                    new_node = StateNode(current_state, number, state, reasons[state_index])
                    current_state.add_child(new_node)
                    print("    found child: {}".format(new_node.number))
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
