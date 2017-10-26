import sys
import model
import pprint

def main():

    option = input("Do you want the extras to added to the model (yes/no)? ")

    tap = model.Entity(name="Tap")
    container = model.Entity(name="Container")
    sink = model.Entity(name="Sink")


    inflow = model.Quantity(name="inflow", quantity_space=[
        model.QuantityValue.ZERO,
        model.QuantityValue.POSITIVE])
    tap.add_quantity(inflow)
    volume = model.Quantity(name="volume", quantity_space=[
        model.QuantityValue.ZERO,
        model.QuantityValue.POSITIVE,
        model.QuantityValue.MAX])
    container.add_quantity(volume)
    outflow = model.Quantity(name="outflow", quantity_space=[
        model.QuantityValue.ZERO,
        model.QuantityValue.POSITIVE,
        model.QuantityValue.MAX])
    sink.add_quantity(outflow)

    if (option == "yes"):
        height = model.Quantity(name="height", quantity_space=[
                                                model.QuantityValue.ZERO,
                                                model.QuantityValue.POSITIVE,
                                                model.QuantityValue.MAX])
        container.add_quantity(height)
        pressure = model.Quantity(name="pressure", quantity_space=[
            model.QuantityValue.ZERO,
            model.QuantityValue.POSITIVE,
            model.QuantityValue.MAX])
        container.add_quantity(pressure)

    entities = [
        tap,
        container,
        sink
    ]

    inflow_i = model.InfluenceRelationship(name="inflow_I+",
                                            causal_party=inflow,
                                            receiving_party=volume,
                                            sign=model.Derivative.POSITIVE)
    outflow_i = model.InfluenceRelationship(name="outflow_I-",
                                            causal_party=outflow,
                                            receiving_party=volume,
                                            sign=model.Derivative.NEGATIVE)

    if(option == "yes"):
        pressure_outflow_p = model.ProportionalRelationship(name="pressure_outflow_P+",
                                                            causal_party=pressure,
                                                            receiving_party=outflow,
                                                            sign=model.Derivative.POSITIVE)
        volume_height_p = model.ProportionalRelationship(name="volume_height_P+",
                                                         causal_party=volume,
                                                         receiving_party=height,
                                                         sign=model.Derivative.POSITIVE)
        height_pressure_p = model.ProportionalRelationship(name="height_pressure_P+",
                                                           causal_party=height,
                                                           receiving_party=pressure,
                                                           sign=model.Derivative.POSITIVE)
    else:
        volume_outflow_p = model.ProportionalRelationship(name="volume_outflow_P+",
                                            causal_party=volume,
                                            receiving_party=outflow,
                                            sign=model.Derivative.POSITIVE)

    if(option == "yes"):
        pressure_outflow_eq = model.EquivalenceRelationship(name="pressure_outflow_EQ",
                                                            causal_party=pressure,
                                                            receiving_party=outflow,
                                                            equivalences=[model.QuantityValue.MAX,
                                                                          model.QuantityValue.ZERO])
        height_pressure_eq = model.EquivalenceRelationship(name="height_pressure_EQ",
                                                           causal_party=height,
                                                           receiving_party=pressure,
                                                           equivalences=[model.QuantityValue.MAX,
                                                                         model.QuantityValue.ZERO])
        volume_height_eq = model.EquivalenceRelationship(name="volume_height_EQ",
                                                         causal_party=volume,
                                                         receiving_party=height,
                                                         equivalences=[model.QuantityValue.MAX,
                                                                       model.QuantityValue.ZERO])
    else:
        volume_outflow_eq = model.EquivalenceRelationship(name="volume_outflow_EQ",
                                            causal_party=volume,
                                            receiving_party=outflow,
                                            equivalences=[model.QuantityValue.MAX, model.QuantityValue.ZERO])

    relationships = [
        inflow_i,
        outflow_i
    ]

    if(option == "yes"):
        relationships.append(pressure_outflow_p)
        relationships.append(volume_height_p)
        relationships.append(height_pressure_p)
        relationships.append(volume_height_eq)
        relationships.append(height_pressure_eq)
        relationships.append(pressure_outflow_eq)
    else:
        relationships.append(volume_outflow_p)
        relationships.append(volume_outflow_eq)

    causal_graph = model.CausalGraph(entities=entities, relationships=relationships)

    if(option == "yes"):
        state_graph = model.State_Graph(initial_state=[model.QuantityValue.ZERO,
                                                  model.Derivative.POSITIVE,
                                                  model.QuantityValue.ZERO,
                                                  model.Derivative.ZERO,
                                                  model.QuantityValue.ZERO,
                                                  model.Derivative.ZERO,
                                                  model.QuantityValue.ZERO,
                                                  model.Derivative.ZERO,
                                                  model.QuantityValue.ZERO,
                                                  model.Derivative.ZERO],
                                                  causal_graph=causal_graph)
    else:
        state_graph = model.State_Graph(initial_state=[model.QuantityValue.ZERO,
                                                       model.Derivative.POSITIVE,
                                                       model.QuantityValue.ZERO,
                                                       model.Derivative.ZERO,
                                                       model.QuantityValue.ZERO,
                                                       model.Derivative.ZERO],
                                        causal_graph=causal_graph)
        
    states = state_graph.make_graph()
    print(state_graph)


if __name__ == "__main__":
    sys.exit(main())
