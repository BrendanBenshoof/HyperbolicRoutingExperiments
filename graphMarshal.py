import networkx as nx
import json


def marshal_graph(g):
    output = {"nodes": [], "edges": [], "locs": {}}
    output["nodes"] = list(map(str, g.nodes()))
    output["edges"] = list(map(lambda x: (str(x[0]), str(x[1])), g.edges()))
    output["locs"] = {str(x): g.node[x]["loc"] for x in g.nodes()}
    return output


def unmarshal_graph(d):
    g = nx.DiGraph()
    g.add_nodes_from(d["nodes"])
    for e in d["edges"]:
        g.add_edge(e[0], e[1])
    for n in d["locs"]:
        g.node[n]["loc"] = d["locs"][n]
    return g
