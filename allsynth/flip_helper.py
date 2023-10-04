import sys
import os

sys.path = [s for s in sys.path if "qsynth" not in s]

import flip
import networkx as nx
import time
import argparse
import logging 

#logging.getLogger(flip.__name__).setLevel(-10)
#logging.getLogger(verify.__name__).setLevel(logging.DEBUG)

def compute_sequence_util(p1, p2, subs):
    G_init = nx.DiGraph()
    G_init.add_path(p1)
    G_final = nx.DiGraph()
    G_final.add_path(p2)
    G = flip.Graph(G_init, G_final, dst=p1[-1], srcs=[p1[0]])
    G.subpaths = subs
    
    print("p1: {}".format(p1))
    print("p2: {}".format(p2))
    print("subs: {}".format(subs))
    t = -42
    start = time.time()
    try:
        m = flip.compute_sequence(graph=G, duplicate=False)
        res = m.verify()
    except flip.PreconditionFailedError as e:
        print(e)
    except flip.verify.InvalidNetworkConfigurationError as e:
        print(e)
    except Exception as e:
        print(e)

    end = time.time()
    t = end -start
    print("TIME=" + str(t))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument('-init', dest="init", type=str, nargs="+", required=True)
    parser.add_argument('-final', dest="final", type=str, nargs="+", required=True)
    parser.add_argument('-subpaths', dest="subs", type=str, nargs="+", action='append', required=True)

    args = parser.parse_args()
    p1 = args.init
    p2 = args.final
    subs = args.subs

    # Assumed all arguments are qouted
    p1 = p1[0].split(" ")
    p2 = p2[0].split(" ")
    for s in range(len(subs)):
        subs[s] = subs[s][0].split(" ")

    compute_sequence_util(p1,p2,subs)