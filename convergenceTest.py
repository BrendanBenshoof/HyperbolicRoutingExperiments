import networkx
import random
import threading


class Logic(object):

    def __init__(self, mid, dist, peermin, peermax):
        self.midfunc = mid
        self.distfunc = dist
        self.short_peer_min = peermin
        self.long_peer_max = peermax

    def peerFilter(self, center, others):
        # DGVH
        if(len(others) <= self.short_peer_min):
            return others, []
        candidates = sorted(
            others, key=lambda x: self.distfunc(center.loc, x.loc))
        selected = [candidates[0]]
        candidates = candidates[1:]
        extra = []
        for c in candidates:
            m = self.midfunc(center.loc, c.loc)
            rejected = False
            mydist = self.distfunc(center.loc, m)
            for p in selected:
                if self.distfunc(p.loc, m) < mydist:
                    rejected = True
                    break
            if rejected:
                extra.append(p)
            else:
                selected.append(p)
        if(len(selected) < self.short_peer_min):
            selected = selected + extra[:self.short_peer_min - len(selected)]
            extra = extra[self.short_peer_min - len(selected):]
        if len(extra) < self.long_peer_max:
            extra = random.sample(extra, self.long_peer_max)
        return selected, extra


class Node(object):

    def __init__(loc, dhtLogic):
        self.loc = loc
        self.short_peers = []
        self.long_peers = []
        self.notified = []
        self.PeerLock = threading.Lock()
        self.logic = dhtLogic

    def join(self, bootstraps):
        with self.PeerLock():
            self.short_peers, self.long_peers = self.logic.peerFilter(
                self.loc, bootstraps)

    def getPeers(self):
        with self.PeerLock():
            return self.short_peers[:]

    def notify(self, other):
        with self.PeerLock():
            self.notified.append(other)

    def tick(self):
        new_pool = set(self.short_peers + self.long_peers)
        for p in self.short_peers:
            new_peers = p.getPeers()
            new_pool.update(set(new_peers))
        new_pool.update(set(self.notified))
        with self.PeerLock():
            self.notified = []
            self.short_peers, self._long_peers = self.logic.peerFilter(
                self.loc, list(new_pool))

        for p in self.short_peers:
            p.notify(self)
