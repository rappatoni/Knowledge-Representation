import sys
import model
def main():
    inflow = model.Entity(name="inflow", quantities=frozenset([model.Quantity.ZERO,
                                                    model.Quantity.POSITIVE]))
    volume = model.Entity(name="volume", quantities=frozenset([model.Quantity.ZERO,
                                                    model.Quantity.POSITIVE,
                                                    model.Quantity.MAX]))
    outflow = model.Entity(name="outflow", quantities=frozenset([model.Quantity.ZERO,
                                                    model.Quantity.POSITIVE,
                                                    model.Quantity.MAX]))
    entities = [
        inflow,
        volume,
        outflow
    ]
    inflow_i = model.InfluenceRelationship(name="inflow_I+",
                                            causal_party=inflow,
                                            receiving_party=volume,
                                            sign=model.Quantity.POSITIVE)
    outflow_i = model.InfluenceRelationship(name="outflow_I-",
                                            causal_party=outflow,
                                            receiving_party=volume,
                                            sign=model.Quantity.NEGATIVE)
    volume_p = model.ProportionalRelationship(name="volume_P+",
                                            causal_party=volume,
                                            receiving_party=outflow,
                                            sign=model.Quantity.POSITIVE)
    relationships = [
        inflow_i,
        outflow_i,
        volume_p
    ]
    graph = model.CausalGraph(entities=entities, relationships=relationships)

if __name__ == "__main__":
    sys.exit(main())
