import math
import random
import networkx as nx
from matplotlib import pyplot as plt


def randomPoint(boundRadius=100.0):
    r = random.random()**0.5
          # math.log(1 + random.random() * boundRadius) / math.log(1 +
          # boundRadius)

    theta = 2 * math.pi * random.random()
    x = r * math.sin(theta)
    y = r * math.cos(theta)
    return (x, y)


def fEq(a, b):
    return abs(a - b) <= 0.000001


def dot(a, b):
    return sum(map(lambda x, y: x * y, a, b))


def cross(a):
    # assumes 2d
    return (-1 * a[1], a[0])


def klein2poincare(s):
    assert(dot(s, s) < 1)
    return tuple(map(lambda x: x / (1 + (1 - dot(s, s))**0.5), s))


def poincare2klein(u):
    assert(dot(u, u) < 1)
    return tuple(map(lambda x: (x * 2) / (1 + dot(u, u)), u))


def eMid(a, b):
    return tuple(map(lambda x, y: (x + y) / 2, a, b))


def eDist(a, b):
    return sum(map(lambda x, y: (x - y)**2.0, a, b))**0.5


def hDist(a, b):

    sigma = 2 * eDist(a, b)**2.0 / ((1 - dot(a, a)) * (1 - dot(b, b)))
    return math.acosh(1 + sigma)


def normalize(vec):

    mag = dot(vec, vec)**0.5
    return tuple(map(lambda x: x / mag, vec))


def point2lineDist(p0, p1, p2):
    # p1 and p2 form a line
    return math.fabs((p2[1] - p1[1]) * p0[0] -
                     (p2[0] - p1[0]) * p0[1] + p2[0] * p1[1] - p2[1] * p1[0]) /\
        eDist(p1, p2)


def kleinIdealPts(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dr = (dx * dx + dy * dy)**0.5
    D = a[0] * b[1] - b[0] * a[1]
    x_0 = (D * dy + dx * (dr * dr - D * D)**0.5) / (dr * dr)
    x_1 = (D * dy - dx * (dr * dr - D * D)**0.5) / (dr * dr)
    y_0 = (-1 * D * dx + dy * (dr * dr - D * D)**0.5) / (dr * dr)
    y_1 = (-1 * D * dx - dy * (dr * dr - D * D)**0.5) / (dr * dr)

    secant_candiates = list(
        set([(x_0, y_0), (x_1, y_0), (x_0, y_1), (x_1, y_1)]))
    output = []
    for s in secant_candiates:
        if fEq(point2lineDist(s, a, b), 0) and fEq(dot(s, s), 1.0):
            output.append(s)
            if(len(output) == 2):
                break
    assert(len(output) == 2)
    return output


def lineIntersect(p1, p2, p3, p4):
    pole_x = 0
    pole_y = 0
    try:
        pole_x = ((p1[0] * p2[1] - p1[1] * p2[0]) * (p3[0] - p4[0]) - (p1[0] - p2[0]) * (p3[0] * p4[1] - p3[1] * p4[0])) / (
            (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0]))
    except:
        print("parallel")
        pole_x = float("inf")
        return (pole_x, poley)
    try:
        pole_y = ((p1[0] * p2[1] - p1[1] * p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] * p4[1] - p3[1] * p4[0])) / (
            (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0]))
    except:
        print("parallel")
        pole_y = float("inf")
        return (pole_x, poley)

    pole = (pole_x, pole_y)

    assert(fEq(point2lineDist(pole, p1, p2), 0))
    assert(fEq(point2lineDist(pole, p3, p4), 0))

    return pole


def kleinPole(a, b):
    p1, p3 = kleinIdealPts(a, b)
    p2 = map(lambda x, y: x + y, p1, cross(p1))
    p4 = map(lambda x, y: x + y, p3, cross(p3))
    pole = lineIntersect(p1, p2, p3, p4)
    assert(fEq(eDist(p1, pole), eDist(p3, pole)))
    return pole


def hMid(a, b):
    k_a = poincare2klein(a)
    k_b = poincare2klein(b)
    assert(dot(k_a, k_a) < 1.0)

    assert(dot(k_b, k_b) < 1.0)
    pole = kleinPole(k_a, k_b)
    a_pts = sorted(kleinIdealPts(pole, k_a), key=lambda x: eDist(x, pole))
    b_pts = sorted(kleinIdealPts(pole, k_b), key=lambda x: eDist(x, pole))
    mid = (0, 0.99999)
    for p0 in a_pts:
        for p1 in b_pts:
                test_mid = lineIntersect(a_pts[0], b_pts[1], k_a, k_b)
                if dot(test_mid, test_mid) < 1.0 and fEq(hDist(k_a, test_mid), hDist(k_b, test_mid)):
                    mid = test_mid
    # if not fEq(hDist(k_a, mid), hDist(k_b, mid)):
    #    print(hDist(k_a, mid), hDist(k_b, mid))
    # assert(fEq(hDist(k_a, mid), hDist(k_b, mid)))
    return klein2poincare(mid)


def plotPoints(pointlist, g=None):
    if g is None:
        g = nx.Graph()
        g.add_nodes_from(pointlist)
    locdict = {x: x for x in pointlist}
    nx.draw(g, pos=locdict)
    plt.show()
    return g


def EuclidianfastDGVH(pointlist):
    g = nx.DiGraph()
    g.add_nodes_from(pointlist)
    for p in pointlist:
        canidates = pointlist[:]
        canidates.remove(p)
        canidates = sorted(canidates, key=lambda x: eDist(x, p))

        short_peers = [canidates[0]]
        canidates.remove(canidates[0])
        for c in canidates:
            c_m = eMid(p, c)
            # print(c_m)
            best_peer = min(short_peers, key=lambda x: eDist(x, c_m))
            if(eDist(best_peer, c_m) > eDist(p, c_m)):
                short_peers.append(c)
        for c in short_peers:
            g.add_edge(p, c)
    return g


def HyperfastDGVH(pointlist):
    g = nx.DiGraph()
    g.add_nodes_from(pointlist)
    for p in pointlist:
        canidates = pointlist[:]
        canidates.remove(p)
        canidates = sorted(canidates, key=lambda x: hDist(x, p))

        short_peers = [canidates[0]]
        canidates.remove(canidates[0])
        for c in canidates:
            c_m = hMid(p, c)
            best_peer = min(short_peers, key=lambda x: hDist(x, c_m))
            if(hDist(best_peer, c_m) > hDist(p, c_m)):
                short_peers.append(c)
        for c in short_peers:
            g.add_edge(p, c)
    return g


def hyperDelta(p, delta):
    n_p = tuple(map(lambda x, y: x + y, p, delta))
    dist = 100.0
    try:
        dist = hDist(p, n_p)
    except:
        pass
    if dist > 1.0:
        return hyperDelta(p, tuple(map(lambda x: 0.5 * x, delta)))
    return n_p


def hyperEmbed(g):
    locs = {x: randomPoint() for x in g.nodes()}
    rev_locs = {locs[x]: x for x in locs.keys()}
    MAX_iter = 100
    for i in range(0, MAX_iter):
        print(i)
        overlay = HyperfastDGVH(rev_locs.keys())
        newlocs = {}
        for p in g.nodes():
            ploc = locs[p]
            force = [0.0, 0.0]
            total_hDist = 0.0
            total_realdist = 0.0
            weight = 0.0
            for locq in overlay.nodes():
                q = rev_locs[locq]
                if p == q:
                    continue
                qloc = locs[q]
                dist = hDist(ploc, qloc)
                ideal_dist = nx.astar_path_length(g, p, q) * 0.5
                w = eDist((0, 0), qloc)
                delta_f = (ideal_dist - dist) * 0.1 * (
                    1.0 - float(i) / MAX_iter) * w
                weight += w
                force[0] -= (qloc[0] - ploc[0]) * delta_f
                force[1] -= (qloc[1] - ploc[1]) * delta_f

            force[0] /= weight
            force[1] /= weight
            newlocs[p] = hyperDelta(ploc, force)
        locs = newlocs
        rev_locs = {locs[x]: x for x in locs.keys()}
    print(isGreedy(HyperfastDGVH(rev_locs.keys()), hDist))
    return locs


def isGreedy(g, dfunc):
    size = len(g.nodes())

    def greedySeek(a, b, g):
        steps = 0
        current = a
        while steps < size:
            nextHop = min(g.neighbors(current), key=lambda x: dfunc(x, b))
            current = nextHop
            if(current == b):
                return steps
            steps += 1
        return float("inf")
    total_worst = 0.0
    for n0 in g.nodes():
        for n1 in g.nodes():
            if n0 != n1:
                total_worst += greedySeek(n0, n1, g)

    return total_worst / (size * (size - 1))


def isGreedywLocs(g, locs, dfunc):
    size = len(g.nodes())

    def greedySeek(a, b, g):
        steps = 0
        current = a
        while steps < size:
            nextHop = min(
                g.neighbors(current), key=lambda x: dfunc(locs[x], locs[b]))
            current = nextHop
            if(current == b):
                return steps
            steps += 1
        return float("inf")

    total_worst = 0.0
    for n0 in g.nodes():
        for n1 in g.nodes():
            if n0 != n1:
                total_worst += greedySeek(n0, n1, g)

    return total_worst / (size * (size - 1))

"""
points = [randomPoint() for x in range(10)]
g = HyperfastDGVH(points)
print(isGreedy(g, hDist))
plotPoints(points, g)
degrees = {}
for p in g:
    degree = len(g.neighbors(p))
    if degree in degrees.keys():
        degrees[degree] += 1
    else:
        degrees[degree] = 1
degree_seq = [0] * (max(degrees.keys()) + 1)
for k in degrees.keys():
    degree_seq[k] = degrees[k]
plt.plot(degree_seq)
plt.show()

"""
g = nx.balanced_tree(5, 2)

tmp_locs = hyperEmbed(g)

nx.draw(g, pos=tmp_locs, labels={x: x for x in g.nodes()})
plt.show()
