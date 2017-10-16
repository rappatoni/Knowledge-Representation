import sys
import model

def main():
    inflow = model.Entity(name="inflow", quantities=frozenset([model.QuantitySpace.ZERO,
                                                    model.QuantitySpace.POSITIVE]))
    volume = model.Entity(name="volume", quantities=frozenset([model.QuantitySpace.ZERO,
                                                    model.QuantitySpace.POSITIVE,
                                                    model.QuantitySpace.MAX]))
    outflow = model.Entity(name="outflow", quantities=frozenset([model.QuantitySpace.ZERO,
                                                    model.QuantitySpace.POSITIVE,
                                                    model.QuantitySpace.MAX]))
    entities = [
        inflow,
        volume,
        outflow
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

    graph = model.CausalGraph(entities=entities, relationships=relationships)
    graph.traverse_graph(initial_state= ([model.QuantitySpace.ZERO,
                                                  model.Derivative.POSITIVE,
                                                  model.QuantitySpace.ZERO,
                                                  model.Derivative.ZERO,
                                                  model.QuantitySpace.ZERO,
                                                  model.Derivative.ZERO]))

if __name__ == "__main__":
    sys.exit(main())
