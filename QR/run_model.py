import sys
import model

def main():

    tap = model.Entity(name="Tap")
    container = model.Entity(name="Container")
    sink = model.Entity(name="Sink")

    tap.add_quantity(name="inflow", quantities=frozenset([model.QuantitySpace.ZERO,
                                                    model.QuantitySpace.POSITIVE]))
    container.add_quantity(name="volume", quantities=frozenset([model.QuantitySpace.ZERO,
                                                    model.QuantitySpace.POSITIVE,
                                                    model.QuantitySpace.MAX]))
    sink.add_quantity(name="outflow", quantities=frozenset([model.QuantitySpace.ZERO,
                                                    model.QuantitySpace.POSITIVE,
                                                    model.QuantitySpace.MAX]))
    entities = [
        tap,
        container,
        sink
    ]

    inflow_i = model.InfluenceRelationship(name="inflow_I+",
                                            causal_party=tap.quantities[0],
                                            receiving_party=container.quantities[0],
                                            sign=model.Derivative.POSITIVE)
    outflow_i = model.InfluenceRelationship(name="outflow_I-",
                                            causal_party=sink.quantities[0],
                                            receiving_party=container.quantities[0],
                                            sign=model.Derivative.NEGATIVE)
    volume_p = model.ProportionalRelationship(name="volume_P+",
                                            causal_party=container.quantities[0],
                                            receiving_party=sink.quantities[0],
                                            sign=model.Derivative.POSITIVE)
    relationships = [
        inflow_i,
        outflow_i,
        volume_p
    ]

    graph = model.CausalGraph(entities=entities, relationships=relationships)
    graph.traverse_graph(initial_state= ([model.QuantitySpace.ZERO,
                                                  model.Derivative.POSITIVE,
                                                  model.QuantitySpace.ZERO,
                                                  model.Derivative.ZERO,
                                                  model.QuantitySpace.ZERO,
                                                  model.Derivative.ZERO]))

if __name__ == "__main__":
    sys.exit(main())
