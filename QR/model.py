from enum import Enum, unique
from PIL import Image, ImageDraw, ImageFont

class CausalGraph:

    def __init__(self, entities, relationships):
        # list of Entity
        self.entities = entities
        # list of relationships
        self.relationships = relationships

    #def draw_graph(self, state):
    def draw_graph(self):
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
        return image

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
        #Am I correct in assuming that quantities= comparison group = quantity space (in Dynalearn)?
        #If so, should we not add an attribute quantity? An entity can have multiple quanitities, each with its own
        #quantity space and current magnitude. This isn't a necessary functionality now but will be needed for
        #the "extra" stuff.
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

    def apply_derviate(self):
        #Shouldn't it be greater or equal?
        if self.deriviate > Quantity.POSITIVE:
            return self.increase_magnitude()
        elif self.deriviate == Quantity.ZERO:
            return self.current_magnitude
        else:
            return self.decrease_magnitude()


    def __str__(self):
        return "name={}, derivate={}, current_magnitude={}".format(self.name, self.derivate, self.current_magnitude)
