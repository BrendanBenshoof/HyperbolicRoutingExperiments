import networkx as nx
import matplotlib.pyplot as plt

from graphMarshal import unmarshal_graph

from convergenceTest import *

try:
    import cPickle as pickle
except ImportError:
    import pickle


def Diameter_series(path):
    with open(path, "r") as fp:
        graphs = map(unmarshal_graph, json.load(fp))
        ticks = []
        i = 0
        diameters = []
        for g in graphs:
            nx.draw(g, pos={x: g.node[x]['loc'] for x in g.nodes()})
            plt.show()
            print(i)
            ticks.append(i)
            diameters.append(nx.diameter(g))
            i += 1
        plt.plot(ticks, diameters)
        plt.show()


Diameter_series("test.json")
