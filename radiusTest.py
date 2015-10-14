import networkx as nx
import random
import threading

import json

import math

from graphMarshal import marshal_graph

from multiprocessing.pool import ThreadPool

import HyperbolicSpaceMath as H

HASHMAX = 2**160


def circle_random():
    theta = random.random() * 2 * math.pi
    r = random.random()**2.0
    return math.sin(theta) * r, math.cos(theta) * r


def hash_random():
    return int(random.random() * HASHMAX)


def chordDist(a, b):
    return math.fabs(a, b)


class Logic(object):

    def __init__(self, mid, dist, peermin, peermax):
        self.midfunc = mid
        self.distfunc = dist
        self.short_peer_min = peermin
        self.long_peer_max = peermax

    def longPeerFilter(self, center, others):
        if len(others) > self.long_peer_max:
            return random.sample(others, self.long_peer_max)
        else:
            return others

    def peerFilter(self, center, others):
        # DGVH
        if(len(others) <= self.short_peer_min):
            #print("not enough peers!")
            return others, []
        candidates = sorted(
            others, key=lambda x: self.distfunc(center, x.loc))
        selected = [candidates[0]]
        candidates.remove(selected[0])
        extra = []
        for c in candidates:
            mydist = self.distfunc(center, c.loc)
            for p in selected:
                if self.distfunc(p.loc, c.loc) < mydist:
                    rejected = True
                    break
            if rejected:
                extra.append(c)
            else:
                selected.append(c)
        #assert(len(selected) + len(extra) == len(others))
        if(len(selected) < self.short_peer_min):
            selected = selected + extra[:self.short_peer_min - len(selected)]
            extra = extra[self.short_peer_min - len(selected):]

        return selected, self.longPeerFilter(center, extra)


class Node(object):

    def __init__(self, loc, dhtLogic):
        self.loc = loc
        self.short_peers = []
        self.long_peers = []
        self.notified = []
        self.logic = dhtLogic

    def render(self):
        return self.loc

    def join(self, bootstraps):
        self.short_peers = bootstraps[:]

    def getPeers(self):
        return list(set(self.short_peers))

    def notify(self, other):
        self.notified.append(other)

    def tick(self):
        new_pool = set(self.short_peers + self.long_peers + self.notified)
        self.notified = []
        for p in self.short_peers:
            new_peers = p.getPeers()
            new_pool.update(set(new_peers))
        if self in new_pool:
            new_pool.remove(self)
        #assert(len(new_pool) >= len(set(self.short_peers + self.long_peers)))
        self.short_peers, self.long_peers = self.logic.peerFilter(
            self.loc, list(new_pool))
        #print(len(new_pool), len(set(self.short_peers + self.long_peers)))
        #assert(len(new_pool) == len(set(self.short_peers + self.long_peers)))

        for p in self.short_peers:
            p.notify(self)
        #print(len(self.short_peers) + len(self.long_peers))


def RunTrial(peerLogic, rlockfunc, outpath, size=200, ticksperjoin=20):
    workers = ThreadPool(size)
    output = []
    nodes = [Node(rlockfunc(), peerLogic)]
    g = nx.DiGraph()
    for i in range(size):
        newnode = Node(rlockfunc(), peerLogic)
        newnode.join(nodes)
        nodes.append(newnode)

        gprime = nx.DiGraph()
        gprime.add_nodes_from(nodes)
        for j in range(ticksperjoin):
            workers.map(lambda x: x.tick(), nodes)
        for n in nodes:
            gprime.node[n]["loc"] = n.loc
            for p in n.getPeers():
                gprime.add_edge(n, p)
        output.append(gprime)
        print(i)
    with open(outpath, "w") as fp:
        json.dump(list(map(marshal_graph, output)), fp)


def euclid_random():
    return (random.random(), random.random())


def euclid_mid(a, b):
    return b  # list(map(lambda x, y: (x + y) / 2, a, b))


def euclid_dist(a, b):
    return sum(map(lambda x, y: (x - y)**2.0, a, b))**0.5

if __name__ == "__main__":
    random.seed(0)
    euclid_Logic = Logic(lambda x, y: y, H.hDist, 4, 16)
    RunTrial(euclid_Logic, circle_random, "Hyperincreasing_size.json", size=50)
