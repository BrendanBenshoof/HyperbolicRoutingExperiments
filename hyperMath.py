import math
import random
import networkx as nx
from matplotlib import pyplot as plt

def RandomPoint(boundRadius=1000000.0):
    r = random.random()**0.5

    theta = 2*math.pi*random.random()
    x = r*math.sin(theta)
    y = r*math.cos(theta)
    return (x,y)

def eMid(a,b):
    return tuple(map(lambda x,y: (x+y)/2, a,b))

def eDist(a,b):
    return sum(map(lambda x,y: (x-y)**2.0, a, b))**0.5

def hDist(a,b):
    sigma = 2*eDist(a,b)**2.0/( (1-eDist((0,0),a)**2.0)*(1-eDist((0,0),b)**2.0)   )
    return math.acosh(1+sigma)

def hMid(a,b):
    def subMid(a,b,c):
        ideal = hDist(a,b)/2.0
        c_0 = eMid(a,c)
        c_1 = eMid(c,b)
        error_0 = (hDist(a,c_0)-ideal)**2.0+(hDist(b,c_0)-ideal)**2.0
        error_1 = (hDist(a,c_1)-ideal)**2.0+(hDist(b,c_1)-ideal)**2.0
        print(error_0)
        if error_0 < error_1:
            if(error_0<1.0):
                return c_0
            else:
                return subMid(a,b,c_0)
        else:
            if(error_1<1.0):
                return c_1
            else:
                return subMid(a,b,c_1)
    return subMid(a,b,eMid(a,b))

def plotPoints(pointlist,g=None):
    if g is None:
        g = nx.Graph()
        g.add_nodes_from(pointlist)
    locdict = {x:x for x in pointlist}
    nx.draw(g,pos=locdict)
    plt.show()
    return g

def EuclidianfastDGVH(pointlist):
    g = nx.DiGraph()
    g.add_nodes_from(pointlist)
    for p in pointlist:
        canidates = pointlist[:]
        canidates.remove(p)
        canidates = sorted(canidates,key=lambda x: eDist(x,p))

        short_peers = [canidates[0]]
        canidates.remove(canidates[0])
        for c in canidates:
            c_m = eMid(p,c)
            print(c_m)
            best_peer = min(short_peers,key=lambda x: eDist(x,c_m))
            if(eDist(best_peer,c_m)>eDist(p,c_m)):
                short_peers.append(c)
        for c in short_peers:
            g.add_edge(p,c)
    return g

def HyperfastDGVH(pointlist):
    g = nx.DiGraph()
    g.add_nodes_from(pointlist)
    for p in pointlist:
        canidates = pointlist[:]
        canidates.remove(p)
        canidates = sorted(canidates,key=lambda x: hDist(x,p))

        short_peers = [canidates[0]]
        canidates.remove(canidates[0])
        for c in canidates:
            c_m = hMid(p,c)
            print(p,c_m)
            best_peer = min(short_peers,key=lambda x: hDist(x,c_m))
            if(eDist(best_peer,c_m)>hDist(p,c_m)):
                short_peers.append(c)
        for c in short_peers:
            g.add_edge(p,c)
    return g

def hyperDelta(p,delta):
    n_p = tuple(map(lambda x,y: x+y),p,delta)
    if hDist(p,n_p)>1.0:
        return hyperDelta(p,tuple(map(lambda x: 0.5*x, delta)))
    return n_p


def hyperEmbed(g):
    locs = {x:randomPoint() for x in g.nodes()}
    for i in range(0,100):
        for p in g.nodes():
            ploc = locs[p]
            force = [0.0,0.0]
            for q in p.nodes():
                if p==q:
                    continue
                qloc = locs[q]
                dist = hDist(ploc,qloc)


points = [RandomPoint() for x in range(100)]
g = EuclidianfastDGVH(points)
plotPoints(points,g)
