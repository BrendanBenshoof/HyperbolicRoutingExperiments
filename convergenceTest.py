import networkx as nx
import random
import threading

try:
    import cPickle as pickle
except ImportError:
    import pickle

from multiprocessing.pool import ThreadPool


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
            m = self.midfunc(center, c.loc)
            rejected = False
            mydist = self.distfunc(center, m)
            for p in selected:
                if self.distfunc(p.loc, m) < mydist:
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

    def join(self, bootstraps):
        self.short_peers = bootstraps[:]

    def getPeers(self):
        return list(set(self.short_peers + self.long_peers))

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


def RunTrial(peerLogic, rlockfunc, outpath, size=100,
             random_peers=10, iterations=100):
    workers = ThreadPool(size)
    output = []
    nodes = [Node(rlockfunc(), peerLogic) for x in range(size)]
    for n in nodes:
        others = nodes[:]
        others.remove(n)
        n.join(random.sample(others, random_peers))
        # print(len(n.getPeers()))
    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    for n in nodes:
        g.node[n]['loc'] = n.loc
        for p in n.getPeers():
            g.add_edge(n, p)
    output.append(g)
    for i in range(iterations):
        workers.map(lambda x: x.tick(), nodes)
        g = nx.DiGraph()
        g.add_nodes_from(nodes)
        for n in nodes:
            g.node[n]['loc'] = n.loc
            for p in n.getPeers():
                g.add_edge(n, p)
        output.append(g)
    with open(outpath, "wb") as fp:
        pickle.dump(output, fp)
    print(i)


def euclid_random():
    return (random.random(), random.random())


def euclid_mid(a, b):
    return list(map(lambda x, y: (x + y) / 2, a, b))


def euclid_dist(a, b):
    return sum(map(lambda x, y: (x - y)**2.0, a, b))**0.5

if __name__ == "__main__":
    random.seed(0)
    euclid_Logic = Logic(euclid_mid, euclid_dist, 3, 0)
    RunTrial(euclid_Logic, euclid_random, "test.json")
