import networkx
import random


class Node(object):

    def __init__(loc, dhtLogic):
        self.loc = loc
        self.short_peers = []
        self.long_peers = []
        self.notified = []
        self.logic = dhtLogic

    def join(self, bootstraps):
        self.short_peers, self.long_peers = self.logic.peerFilter(
            self.loc, bootstraps)

    def getPeers(self):
        return self.short_peers[:]

    def notify(self, other):
        self.notified.append(other)

    def tick(self):
        new_pool = set(self.short_peers + self.long_peers)
        for p in self.short_peers:
            new_peers = p.getPeers()
            new_pool.update(set(new_peers))
        new_pool.update(set(self.notified))
        self.notified = []
        self.short_peers, self._long_peers = self.logic.peerFilter(
            self.loc, list(new_pool))
        for p in self.short_peers:
            p.notify(self)
