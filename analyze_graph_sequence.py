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
        nexthop = min(hops, key=lambda x: dist(target, g.node[x]["loc"]))
        if nexthop == b:
            break
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
    return greedyReach(*args)


def Diameter_series(path):
    workers = Pool(4)
    with open(path, "r") as fp:
        graphs = list(map(unmarshal_graph, json.load(fp)))
        ticks = []
        i = 0
        diameters = []
        avgDist = []
        hitrate = []
        maxDegree = []
        meanDegree = []
        for g in graphs:
            # nx.draw(g, pos={x: g.node[x]['loc'] for x in g.nodes()})
            # plt.show()
            print(i)
            ticks.append(i)

            s_size = 100
            s_size = min([len(g.nodes()), s_size])
            results = workers.map(wrapper, zip(
                [g] * s_size, random.sample(g.nodes(), s_size), random.sample(g.nodes(), s_size), [XORdist] * s_size))
            total = sum(results) / s_size
            print(total)
            avgDist.append(total)
            if total < float("inf"):
                hitrate.append(1.0)
            else:
                total_hits = 0.0
                for v in results:
                    if v < float("inf"):
                        total_hits += 1.0
                hitrate.append(total_hits / len(results))
            degree_sequence = sorted(nx.degree(g).values(), reverse=True)
            maxDegree.append(max(degree_sequence))
            meanDegree.append(sum(degree_sequence) / len(degree_sequence))

            try:

                diameters.append(nx.diameter(g))
            except:
                diameters.append(float("inf"))

            i += 1
        # g = graphs[-1]
        # nx.draw(g, pos={x: (math.sin(math.pi * 2 * g.node[x]['loc'][0] / HASHMAX), math.cos(
            # math.pi * 2 * g.node[x]['loc'][0] / HASHMAX)) for x in g.nodes()})
        # nx.draw(g, labels={x: (100 * g.node[x]["loc"][0]) // HASHMAX for x in g.nodes()})
        output = {"ticks": ticks, "diameters": diameters, "greedydist": avgDist,
                  "hitrate": hitrate, "maxdegree": maxDegree, "meanDegree": meanDegree}
        with open("data_" + path, "w") as fp:
            json.dump(output, fp)


if __name__ == "__main__":
    workers = Pool(4)
    targets = ["join_chord_1_500_.json", "join_chord_1_1000_.json", "join_chord_3_1000_.json""join_chord_3_500_.json", "join_euclid_1_500_.json", "join_euclid_3_500_.json", "join_hyper_1_500_.json", "join_hyper_3_500_.json", "join_kad_1_500_.json", "join_kad_3_500_.json", "krand_chord_10_1000_.json", "krand_chord_10_100_.json", "krand_chord_10_500_.json", "krand_chord_20_1000_.json", "krand_chord_20_100_.json", "krand_chord_20_500_.json",
               "krand_euclid_10_1000_.json", "krand_euclid_10_100_.json", "krand_euclid_10_500_.json", "krand_euclid_20_1000_.json", "krand_euclid_20_100_.json", "krand_euclid_20_500_.json", "krand_hyper_10_1000_.json", "krand_hyper_10_100_.json", "krand_hyper_10_500_.json", "krand_kad_10_1000_.json", "krand_kad_10_100_.json", "krand_kad_10_500_.json", "krand_kad_20_1000_.json", "krand_kad_20_100_.json", "krand_kad_20_500_.json"]
    workers.map(Diameter_series, targets)
