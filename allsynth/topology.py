import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt
import copy
import os

TOPZOO_PATH = "./topologies/topzoo"
FATTREE_PATH = "./topologies/fattree"
BCUBE_PATH = "./topologies/b-cube"
XPENDER_PATH = "./topologies/xpender"

class DisconnectedError(Exception):
    """Graph is disconnected"""

def get_gml_network(gml_path):
    return nx.read_gml(str(Path(gml_path).resolve()), label='id')

def get_shortest_path_edges(top, path):
    path_pairs = zip(path[0:],path[1:])
    edges = []

    for (n,m) in path_pairs:
        edge = sorted(top[n][m], key=lambda x:top[n][m][x]['weight'])[0]
        edges.append((n,m,edge))

    return edges

def draw_gml_network(G, filename, use_lat_long=False):
    if use_lat_long:
        nx.draw(G,pos={n[0]: (n[1]['Longitude'],n[1]['Latitude']) for n in G.nodes(data=True)  })
    else:
        pos = nx.spring_layout(G)
        nx.draw(G,with_labels=True, node_size=10, font_size=8)
    plt.savefig(filename)  
    plt.close()

def draw_paths(G, p1, p2, filename, draw_top=True, use_lat_long=False):
    edges_p1 = [(p1[i],p1[i+1]) for i in range(len(p1)-1)] 
    edges_p2 = [(p2[i],p2[i+1]) for i in range(len(p2)-1)] 

    if use_lat_long:
        pos = dict()
        first = tuple()
        for n in G.nodes(data=True):
            if 'Longitude' in n[1] and 'Latitude' in n[1]:
                pos[n[0]] = (n[1]['Longitude'],n[1]['Latitude'])
                if len(first) == 0:
                    first = pos[n[0]]
            else:
                pos[n[0]] = first        
    else:
        pos = nx.spring_layout(G)

    if not draw_top:
        G = G.subgraph(p1+p2)

    nx.draw(G, with_labels=True, pos = pos, node_size = 10, font_size=8)
    nx.draw_networkx_edges(G,edgelist=edges_p1, pos=pos, edge_color='r', width=5)
    nx.draw_networkx_edges(G,edgelist=edges_p2, pos=pos, edge_color='g', width=2.5)

    plt.savefig(filename + ".svg", format="svg")
    plt.close()

def gen_topology(p1,p2,weighted=True):
    # Assumes that no multi-edge exists
    top = nx.MultiDiGraph()

    p1_path = list(zip(p1, p1[1:]))
    p2_path = list(zip(p2, p2[1:]))

    if weighted:
        p1_path = [(n,m, {"weight": 1}) for n,m in p1_path]
        p2_path = [(n,m, {"weight": 1}) for n,m in p2_path]

    top.add_edges_from(p1_path)
    top.add_edges_from(p2_path)

    if weighted:
        p1_new_path = [(n,m,0) for n,m,w in p1_path]
        p2_new_path = [(n,m,0) for n,m,w in p2_path]
    else:
        p1_new_path = [(n,m,0) for n,m in p1_path]
        p2_new_path = [(n,m,0) for n,m in p2_path]

    return top, p1_new_path, p2_new_path

def concatenate(G, num_times):
    #draw_gml_network(G, "original")
    G_old = copy.deepcopy(G) 
    for i in range(num_times):
        offset = max(G.nodes()) + 1

        #print("offset : {}".format(offset))

        mapping = {n : n + offset for n in range(len(G_old.nodes()))}
        to_add = nx.relabel_nodes(G_old,mapping)

        periph_G = nx.periphery(G)

        #print("Periph: {}".format(periph_G))
        src = periph_G[0] + offset
        dst = periph_G[-1]

        #print("src:{}".format(src))
        #print("dst:{}".format(dst))
        G = nx.union(G, to_add)

        G.add_edge(dst, src)
        G.add_edge(src, dst)
    
    return G

def get_all_topzoo_nontrivial(num_copies=0):
    topfiles = get_all_topzoo_files()

    n = 0
    good_ones = []
    for top in range(len(topfiles)):
        G, p1, p2 = gen_init_final(topfiles[top], num_copies=num_copies)

        #if p1 != p2:
        good_ones.append((topfiles[top].replace(TOPZOO_PATH, ""), G, p1,p2))
    return good_ones   

def get_all_topzoo_files():
    topfiles = []
    # Not connected graphs  
    bad = {"BtLatinAmerica.gml","Eunetworks.gml", "Padi.gml","UsSignal.gml",
            "Oteglobe.gml","Ntt.gml","Ntelos.gml","KentmanApr2007.gml","Tw.gml",
            "DialtelecomCz.gml","KentmanAug2005.gml","Nsfcnet.gml","Telcove.gml","Bandcon.gml",
            "JanetExternal.gml","Zamren.gml","DeutscheTelekom.gml","Nordu2010.gml","Easynet.gml"} 

    skip = {TOPZOO_PATH + "/" + b for b in bad}

    # Get all GML files in TOPZOO_PATH directory
    for entry in os.scandir(TOPZOO_PATH):
        if entry.path.endswith(".gml") and entry.is_file() and entry.path not in skip:
            topfiles.append(entry.path)
    return topfiles

def gen_init_final(gml_path, src=None, dst=None, num_copies=0):
    G = get_gml_network(gml_path) 
    G = nx.MultiGraph(G)

    if nx.is_connected(G) is False:
        raise DisconnectedError("Graph {} must be connected".format(gml_path))

    if num_copies > 0:
        G = concatenate(G,num_copies)
        assert nx.is_connected(G)
    
    if src == None and dst == None:
        periphery = nx.periphery(G)

        src = periphery[0]
        dst = periphery[-1]

    for e in G.edges:
        s,d,i = e
        G[s][d][i]['weight'] = 1
   
    p1 = nx.dijkstra_path(G, src, dst, 'weight')

    G_cp = copy.deepcopy(G) 
    k = 2
    count = 0
    for n in range(len(p1)-1):
        if count > 0 and count % k == 0:
            for i in G_cp[p1[n]][p1[n+1]]:
                G_cp[p1[n]][p1[n+1]][i]['weight'] = 5

        count = count + 1

    p2 = nx.dijkstra_path(G_cp, src, dst, 'weight')
    #draw_paths(G, p1, p2, "test", draw_top=True, use_lat_long=False)
    #print(len(G.nodes))
    return G, p1, p2

def gen_diamondSharedWP(size):
    p1 = [i for i in range(size)]
    p2 = [i+size for i in range(size)]

    p2[-1] = p1[-1]
    p2[0] = p1[0]

    return p1, p2

def gen_confluent(num_copies):
    assert num_copies >= 1

    p1 = [0,1,2,3,4]
    p2 = [0,3,2,1,4]

    for i in range(num_copies-1):
        p1_add = [max(p1)+1+p1[n] for n in range(4)]
        p2_add = [max(p1_add)-1, max(p1_add)-2, max(p1_add)-3,max(p1_add)]

        p1 = p1 + p1_add
        p2 = p2 + p2_add
    
    return p1, p2

def gen_diamondSeparateWP(size):
    p1 = [i for i in range(size)]
    p2 = [i for i in range(size,size*2,1)]

    p2[0] = p1[0]
    p2[-1] = p1[-1]

    return p1, p2

def gen_zigzag(size, inverse=False):
    p1 = [n for n in range(size)]
    pairs = [(n,n+p1[-1]+1) for n in p1[:-1]]
    p2 = [s for n in pairs for s in n] + [p1[-1]]

    if inverse:
        return p2, p1
    else:
        return p1, p2

