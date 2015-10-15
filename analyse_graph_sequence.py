import networkx as nx
import matplotlib.pyplot as plt

from graphMarshal import unmarshal_graph

from convergenceTest import *

HASHBASE = 120
HASHMAX = 2**HASHBASE

try:
    import cPickle as pickle
except ImportError:
    import pickle

from multiprocessing import Pool

import HyperbolicSpaceMath as H


def edist(a, b):
    return sum(map(lambda x, y: (x - y)**2.0, a, b))**0.5


def XORdist(a, b):
    return a[0] ^ b[0]


def chordDist(a, b):
    a = a[0]
    b = b[0]
    delta = b - a
    if delta < 0:
        return HASHMAX + delta
    return delta


def greedyReach(g, a, b, dist):
    if(a == b):
        return 0
    path = [a]
    target = g.node[b]["loc"]
    maxhops = len(g.nodes())
    i = 0
    while i < maxhops:

        hops = list(map(lambda x: x[1], g.out_edges_iter(path[-1])))
        if b in hops:
            break
        nexthop = min(hops, key=lambda x: dist(target, g.node[x]["loc"]))
        if nexthop in path:
            i = maxhops
        path.append(nexthop)
        i += 1
    # print(path, b)
    if i >= maxhops:
        return float("inf")
    else:
        return len(path)


def wrapper(args):
    res = greedyReach(*args)
    if res < float("inf"):
        return 1.0
    else:
        return 0.0


def Diameter_series(path):
    workers = Pool(4)
    with open(path, "r") as fp:
        graphs = list(map(unmarshal_graph, json.load(fp)))
        ticks = []
        i = 0
        diameters = []
        avgDist = []
        for g in graphs:
            # nx.draw(g, pos={x: g.node[x]['loc'] for x in g.nodes()})
            # plt.show()
            print(i)
            ticks.append(i)

            s_size = 100
            s_size = min([len(g.nodes()), s_size])
            results = workers.map(wrapper, zip(
                [g] * s_size, random.sample(g.nodes(), s_size), random.sample(g.nodes(), s_size), [chordDist] * s_size))
            total = sum(results) / s_size
            print(total)
            avgDist.append(total)

            try:

                diameters.append(nx.diameter(g))
            except:
                diameters.append(float("inf"))

            i += 1
        g = graphs[-1]
        nx.draw(g, pos={x: (math.sin(math.pi * 2 * g.node[x]['loc'][0] / HASHMAX), math.cos(
            math.pi * 2 * g.node[x]['loc'][0] / HASHMAX)) for x in g.nodes()})
        #nx.draw(g, labels={x: (100 * g.node[x]["loc"][0]) // HASHMAX for x in g.nodes()})
        plt.show()
        plt.plot(ticks, diameters)
        plt.plot(ticks, avgDist)
        plt.show()

if __name__ == "__main__":
    Diameter_series("kadtest.json")
