from enum import Enum, unique

class CausalGraph:

    def __init__(self, entities, relationships):
        # list of Entity
        self.entities = entities
        # list of relationships
        self.relationships = relationships

    def draw_graph(self, state):
        pass

    def traverse_graph(self, initial_state):
        # we traverse the causal graph and apply relationships and return a list of next states
        pass

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
        old_value = self.receiving_party.deriviate
        new_value = None
        causal_value = self.causal_party.current_magnitude
        if causal_value > Quantity.ZERO:
            if self.sign == Quantity.POSITIVE:
                # I+ and source +
                new_value = self.receiving_party.increase_deriviate()
            else:
                # I+ and source -
                new_value = self.receiving_party.decrease_deriviate()
        elif causal_value == Quantity.ZERO:
            # if there is no influence, we don't change anything
            new_value = old_value
        else:
            if self.sign == Quantity.POSITIVE:
                # I- and source +
                new_value = self.receiving_party.decrease_deriviate()
            else:
                # I- and source -
                new_value = self.receiving_party.increase_deriviate()
        return new_value


class ProportionalRelationship(Relationship):
    def __init__(self, name, causal_party, receiving_party, sign):
        super(ProportionalRelationship, self).__init__(name, causal_party, receiving_party)
        self.sign = sign

    def apply_relationship(self):
        # TODO add checks for already applied change and
        old_value = self.receiving_party.deriviate
        new_value = None
        causal_value = self.causal_party.deriviate
        if causal_value > Quantity.ZERO:
            if self.sign == Quantity.POSITIVE:
                # P+ and source +
                new_value = self.receiving_party.increase_deriviate()
            else:
                # P+ and source -
                new_value = self.receiving_party.decrease_deriviate()
        elif causal_value == Quantity.ZERO:
            # there is a proportional influnce of 0, we get the receiver to zero
            if self.receiving_party.deriviate > causal_value:
                new_value = self.receiving_party.decrease_deriviate()
            elif self.receiving_party.deriviate == causal_value:
                new_value = old_value
            else:
                new_value = self.receiving_party.increase_deriviate()
        else:
            if self.sign == Quantity.POSITIVE:
                # P- and source +
                new_value = self.receiving_party.decrease_deriviate()
            else:
                # P- and source -
                new_value = self.receiving_party.increase_deriviate()
        return new_value


@unique
class Quantity(Enum):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1
    MAX = 2

    def increase(self, comparion_group):
        new_value = self.value + 1
        for single_quantity in comparion_group:
            if single_quantity.value == new_value:
                return True, single_quantity
        return False, self

    def decrease(self, comparion_group):
        new_value = self.value - 1
        for single_quantity in comparion_group:
            if single_quantity.value == new_value:
                return True, single_quantity
        return False, self


class Entity:
    deriviates = frozenset([Quantity.NEGATIVE, Quantity.ZERO, Quantity.POSITIVE])

    def __init__(self, name, quantities):
        self.name = name
        # a set of qualitative quantities
        self.quantities = quantities
        self.deriviate = Quantity.ZERO
        self.current_magnitude = Quantity.ZERO

    #TODO if a deriviate changes twice in a loop, we want to know that but implement checking elsewhere
    def increase_deriviate(self):
        self.deriviate = Quantity.increase(self.deriviate, self.quantities)
        return self.deriviate

    def decrease_deriviate(self):
        self.deriviate = Quantity.decrease(self.deriviate, self.quantities)
        return self.deriviate

    def increase_magnitude(self):
        self.current_magnitude = Quantity.increase(self.current_magnitude, self.quantities)
        return self.current_magnitude

    def decrease_magnitude(self):
        self.current_magnitude = Quantity.decrease(self.current_magnitude, self.quantities)
        return self.current_magnitude

    def __str__(self):
        return "name={}, derivate={}, current_magnitude={}".format(self.name, self.derivate, self.current_magnitude)
