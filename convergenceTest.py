import networkx as nx
import random
import threading

import json

import math

from graphMarshal import marshal_graph

from multiprocessing.pool import ThreadPool

import HyperbolicSpaceMath as H

HASHMAX = 2**32


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
            # print("not enough peers!")
            return others, []
        candidates = sorted(
            others, key=lambda x: self.distfunc(center, x.loc))
        selected = [candidates[0]]
        candidates.remove(selected[0])
        extra = []
        rejected = False
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
        # assert(len(selected) + len(extra) == len(others))
        if(len(selected) < self.short_peer_min):
            selected = selected + extra[:self.short_peer_min - len(selected)]
            extra = extra[self.short_peer_min - len(selected):]

        return selected, self.longPeerFilter(center, extra)


class HyperLogic(Logic):

    def longPeerFilter(self, center, others):
        if len(others) > self.long_peer_max:
            return others[len(others) - self.long_peer_max:]
        else:
            return others


class KadLogic(Logic):

    def longPeerFilter(self, center, others):
        bucketSize = 10
        buckets = {(0, HASHMAX): [center]}
        for o in others:
            mybucket = None
            for b in buckets.keys():
                if o.loc[0] in range(b[0], b[1]):
                    mybucket = b
                    break
            assert(mybucket is not None)
            if(len(buckets[b]) < bucketSize):
                buckets[b].append(o)
            elif center in buckets[b]:  # split the bucket!
                left_b = (b[0], b[0] + (b[1] - b[0]) // 2)
                left_list = []
                right_b = (b[0] + (b[1] - b[0]) // 2, b[1])
                right_list = []
                for thing in buckets[b]:
                    if thing is not center:
                        if thing.loc[0] in range(left_b[0], left_b[1]):
                            left_list.append(thing)
                        else:
                            right_list.append(thing)
                    else:
                        if center[0] in range(left_b[0], left_b[1]):
                            left_list.append(thing)
                        else:
                            right_list.append(thing)
                if o.loc[0] in range(left_b[0], left_b[1]) and len(left_list) < bucketSize:
                    left_list.append(o)
                elif len(right_list) < bucketSize:
                    right_list.append(o)
                buckets[left_b] = left_list
                buckets[right_b] = right_list
                del buckets[b]
        output = []
        for b in buckets.keys():
            output += buckets[b]
        output.remove(center)
        return list(set(output))

    def peerFilter(self, center, others):
        # DGVH
        if(len(others) <= self.short_peer_min):
            # print("not enough peers!")
            return others, []
        candidates = sorted(
            others, key=lambda x: self.distfunc(center, x.loc))
        selected = [candidates[0]]
        candidates.remove(selected[0])
        extra = []
        rejected = False
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
        # assert(len(selected) + len(extra) == len(others))
        if(len(selected) < self.short_peer_min):
            selected = selected + extra[:self.short_peer_min - len(selected)]
            extra = extra[self.short_peer_min - len(selected):]

        return selected, self.longPeerFilter(center, extra)


class ChordLogic(Logic):

    def longPeerFilter(self, center, others):
        output = []
        # print(len(others))
        for i in range(0, 32):
            target = tuple([(center[0] + 2**i) % HASHMAX])
            subject = min(others, key=lambda x: chordDist(target, x.loc))
            if subject not in output:
                output.append(subject)
        return output

    def peerFilter(self, center, others):
        a = min(others, key=lambda x: chordDist(center, x.loc))
        b = max(others, key=lambda x: chordDist(center, x.loc))

        return list(set([a, b] + self.longPeerFilter(center, others))), []


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
        # print(self.notified)
        self.notified = []
        p = random.choice(self.short_peers)
        new_peers = p.getPeers()
        new_pool.update(set(new_peers))
        if self in new_pool:
            new_pool.remove(self)
        # assert(len(new_pool) >= len(set(self.short_peers + self.long_peers)))
        self.short_peers, self.long_peers = self.logic.peerFilter(
            self.loc, list(new_pool))
        # print(len(new_pool), len(set(self.short_peers + self.long_peers)))
        # assert(len(new_pool) == len(set(self.short_peers + self.long_peers)))

        for p in self.short_peers:
            p.notify(self)
        # print(len(self.short_peers) + len(self.long_peers))


def RunTrial(peerLogic, rlockfunc, outpath, size=200,
             random_peers=20, iterations=100):

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
        list(map(lambda x: x.tick(), nodes))
        g = nx.DiGraph()
        g.add_nodes_from(nodes)
        for n in nodes:
            g.node[n]['loc'] = n.loc
            for p in n.getPeers():
                g.add_edge(n, p)
        output.append(g)
        print(i)
    with open(outpath, "w") as fp:
        json.dump(list(map(marshal_graph, output)), fp)


def euclid_random():
    return (random.random(), random.random())


def circle_random():
    theta = random.random() * 2 * math.pi
    r = (random.random() + random.random())
    if r > 1.0:
        r = 2.0 - r
    return math.sin(theta) * r, math.cos(theta) * r


def euclid_mid(a, b):
    return list(map(lambda x, y: (x + y) / 2, a, b))


def euclid_dist(a, b):
    return sum(map(lambda x, y: (x - y)**2.0, a, b))**0.5


def hash_random():
    return tuple([int(random.random() * HASHMAX)])


def chordDist(a, b):
    return min((HASHMAX + b[0] - a[0]) % HASHMAX, (HASHMAX - b[0] + a[0]) % HASHMAX)


def XORdist(a, b):
    return a[0] ^ b[0]

if __name__ == "__main__":
    random.seed(0)
    l = KadLogic(lambda x, y: y, XORdist, 3, 10)
    RunTrial(l, hash_random, "kadtest.json", size=500)
