import networkx as nx
from bddbase import BDDbase

class IdenticalPathsError(Exception):
    """Initial and final path identical, nothing to do."""

class SynthesisProblem:
    # ASSUMES TOP TO BE MULTIGRAPH
    def __init__(self, init, final, prop, restricted=True, top=None):
        if init == final:
            raise IdenticalPathsError("Initial path and final path are identical!")
        self.is_restricted = restricted
        self.prop = prop

        # If no topology specified, init and final are assumed to be list of nodes
        if top == None:
            #assert init != final 

            assert init[0] == final[0]
            assert init[-1] == final[-1] 
            self.init_path = [(init[n],init[n+1],0) for n in range(len(init)-1)]
            self.final_path = [(final[n],final[n+1],0) for n in range(len(final)-1)]

            G = nx.MultiDiGraph()
            G.add_edges_from(list(set(self.init_path).union(self.final_path)))
            self.top = G

        # Otherwise, init and final are assumed to be list of edges.
        else:
            #assert init != final 
            assert init[0][0] == final[0][0]
            assert init[-1][1] == final[-1][1]

            self.init_path = init
            self.final_path = final
            self.top = top

        self.num_nodes = nx.number_of_nodes(self.top)
        self.is_weighted = nx.is_weighted(self.top)

        self.init_succ = {n: (m,i) for (n,m,i) in self.init_path}
        self.init_succ[self.init_path[-1][1]] = None
        self.init_nodes = [n for (n,_,_) in self.init_path] + [self.init_path[-1][1]]

        self.final_succ = {n: (m,i) for (n,m,i) in self.final_path}
        self.final_succ[self.final_path[-1][1]] = None
        self.final_nodes = [n for (n,_,_) in self.final_path] + [self.final_path[-1][1]]

        self.final_only_nodes = {n for n in self.final_nodes if n not in self.init_nodes}
        self.init_only_nodes = {n for n in self.init_nodes if n not in self.final_nodes}

        self.shared_nodes = [n for n in self.init_nodes if n in self.final_nodes]

        self.modify_nodes = set()

        for n in self.shared_nodes:
            if n == self.init_nodes[-1]:
                continue
            
            i1 = self.init_nodes.index(n)
            i2 = self.final_nodes.index(n)

            if self.init_succ[self.init_nodes[i1]] != self.final_succ[self.final_nodes[i2]]:
                self.modify_nodes.add(n)

        self.no_change_nodes = [n for n in self.shared_nodes if n not in self.modify_nodes]

