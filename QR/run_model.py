import sys
import model
import pprint

def main():

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
    volume_p = model.ProportionalRelationship(name="volume_P+",
                                            causal_party=volume,
                                            receiving_party=outflow,
                                            sign=model.Derivative.POSITIVE)
    relationships = [
        inflow_i,
        outflow_i,
        volume_p
    ]

    causal_graph = model.CausalGraph(entities=entities, relationships=relationships)
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
