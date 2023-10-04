import math
from itertools import product, permutations
from dd.cudd import BDD, and_exists
from cost import Cost

class BDDbase:
    def __init__(self, bdd=None):
        if bdd is None:
            self.bdd = BDD(2**30)
            self.bdd.configure(reordering=True)
        else:
            self.bdd = bdd

    def generate(self, problem, collapse=False, bound=None):
        self.collapse = collapse
        self.is_weighted = False
        self.is_restricted = False
        self.problem = problem

        # If weighted graph, generate cost variables
        if problem.is_weighted:
            self.gen_cost_vars(bound)
            self.is_weighted = True

        if problem.is_restricted:
            self.is_restricted = True
        elif self.collapse:
            raise ValueError("Cannot use reduction with unrestricted problems")
        
        # Map from node IDs to internal BDD states
        self.gen_node_map()

        # State BDDs for n states
        self.gen_states() 

        # Transition BDD 
        self.gen_transitions()

        # Generate update BDDs
        self.gen_config_transitions()
    
    def gen_cost_vars(self,bound):
        max_edge_cost = max(dict(self.problem.top.edges).items(), key=lambda x: x[1]['weight'])[1]['weight']
        max_cost = max_edge_cost * (self.problem.num_nodes - 1)
        num_bits = int(math.log(max_cost,2)) + 1 

        # If bound specified, must provide enough bits to represent bound
        if bound != None:
            bound_bits = int(math.log(bound,2)) + 1 
            num_bits = max(num_bits, bound_bits)

        C1 = ['c1_'+str(i) for i in range(num_bits)]
        C2 = [c.replace('c1','c2') for c in C1]
        C3 = [c.replace('c1','c3') for c in C1]
        C4 = [c.replace('c1','c4') for c in C1]

        self.bdd.declare(*C1)
        self.bdd.declare(*C2)
        self.bdd.declare(*C3)
        self.bdd.declare(*C4)

        self.C1 = C1
        self.C2 = C2
        self.C3 = C3
        self.C4 = C4
        self.cost_size = num_bits

    def get_config_successors(self, Z, backtrack=False):
        assert self.is_restricted
        res = []

        if not backtrack:
            pos  = [i for i in Z if Z[i] == True]
        else:
            pos = Z

        for p in pos:
            ls = Z.copy()
            ls[p] = False
            res.append(ls)
        return res

    def config_to_BDD(self, Z):
        res = self.bdd.true
        for z in Z:
            if Z[z]:
                res = res & self.bdd.var(z)
            else:
                res = res & (~self.bdd.var(z))
        return res

    def BDD_to_config(self, bdd):
        return next(self.bdd.pick_iter(bdd))

    def get_start_and_goal(self):
        start_bdd = self.bdd.true
        goal_bdd = self.bdd.true
        if self.is_restricted:
            for z in self.Z:
                goal_bdd = goal_bdd & (~self.bdd.var(z))  
                start_bdd = start_bdd & self.bdd.var(z)
        else:
            for n in self.E:
                for succ in self.E[n]:
                    for e in self.E[n][succ]:
                        if (n,succ,e) in self.problem.init_path:
                            #print("Adding {}-{}-{} to start".format(n,succ,e))
                            start_bdd = start_bdd & self.E[n][succ][e]
                            #for sol in self.bdd.pick_iter(self.E[n][succ][e]):
                            #    print(sol)
                        elif (n,succ,e) in self.problem.final_path:
                            #print("Adding {}-{}-{} to goal".format(n,succ,e))
                            #for sol in self.bdd.pick_iter(self.E[n][succ][e]):
                            #    print(sol)
                            goal_bdd = goal_bdd & self.E[n][succ][e]

                            # Start must include negation of goal expression
                            if (n, succ,e) not in self.problem.init_path:
                                #print("Adding neg {}-{}-{} to start".format(n,succ,e))
                                #for sol in self.bdd.pick_iter(~self.E[n][succ][e]):
                                #    print(sol)
                                start_bdd = start_bdd & (~self.E[n][succ][e])
                        else:
                            pass
                            #print("{}-{}-{} not added to start or goal!!!".format(n,succ,e))

        return start_bdd, goal_bdd

    def gen_node_map(self):
        p1 = self.problem.init_nodes
        p2 = self.problem.final_nodes
        # Map from node ID to state ID
        n_map = {p1[n] : n for n in range(len(p1))}
        n_count = len(p1)

        for n in p2:
            if n not in p1:
                n_map[n] = n_count
                n_count = n_count + 1

        if not self.is_restricted:
            # For unrestricted, nodes outside paths are also used
            other = [n for n in self.problem.top.nodes if n not in p1 and n not in p2]
            for n in other:
                n_map[n] = n_count
                n_count + 1

        self.n_map = n_map

    def gen_states(self):
        n = self.problem.num_nodes
        bdd = self.bdd
        n_vars = math.ceil(math.log(n,2))  # 2^(n_vars) = n 
        X = ['x' + str(i+1) for i in range(n_vars)]
        Y = [x.replace('x','y') for x in X]

        bdd.declare(*X, *Y)
        perm = list(product([False, True],repeat=n_vars))

        S = {}
        k = 0

        # Loop over all nodes and vars
        for i in range(n):
            for j in range(n_vars):
                xj = bdd.var(X[j])
                # If perm says False for node k and var j, negate
                if not perm[k][j]:
                    xj = ~xj
                # If not first var in S[i], conjunction
                if i in S:
                    S[i] = S[i] & xj
                else:
                # Otherwise direct assignment
                    S[i] = xj
            k = k + 1

        # Construct 'primed' states with map x -> y for x in X
        x_to_y = {str(x) : str(x).replace('x','y') for x in X}
        T = {i: bdd.let(x_to_y, S[i]) for i in range(len(S))}

        self.S = S
        self.T = T
        self.X = X
        self.Y = Y

    def gen_edges(self):
        num_edges = 0

        self.Z_map = dict()
        self.Z = []
        self.E = dict()

        for n in self.problem.top.nodes:
            num_edges = 0
            if n == self.problem.init_nodes[-1]:
                continue

            if n in self.problem.no_change_nodes:
                continue

            # All other successors
            for succ in self.problem.top.adj[n]:
                for e in self.problem.top.adj[n][succ]:
                    num_edges = num_edges + 1

                n_vars = math.ceil(math.log(num_edges,2)) 

            # If only one edge, n_vars would be 0
            if (num_edges == 1):
                n_vars = 1

            self.Z_map[n] = ['z' + str(n) + "-" + str(i+1) for i in range(n_vars)]
            self.bdd.declare(*self.Z_map[n])
            self.Z += self.Z_map[n]

        self.E = {}
        
        # Go through all nodes
        for n in self.problem.top.nodes:
            if n == self.problem.init_nodes[-1]:
                continue
            if n in self.problem.no_change_nodes:
                continue

            self.E[n] = {}
            perm = list(product([False, True],repeat=len(self.Z_map[n])))
            k = 0

            # All adjacent
            for succ in self.problem.top.adj[n]:
                self.E[n][succ] = {}
                # All edges
                for e in self.problem.top.adj[n][succ]:
                    self.E[n][succ][e] = self.bdd.true
                    # Create a BDD for the edge
                    for j in range(len(self.Z_map[n])):
                        zj = self.bdd.var(self.Z_map[n][j])
                        # If perm says False for node k and var j, negate
                        if not perm[k][j]:
                            zj = ~zj
                        self.E[n][succ][e] =  self.E[n][succ][e] & zj
                    k = k + 1

    def gen_transitions(self):
        if self.is_restricted:
            self.gen_transitions_restricted()
        else:
            self.gen_transitions_unrestricted()

    def gen_transitions_restricted(self):
        S = self.S
        T = self.T
        bdd = self.bdd
        n_map = self.n_map
        problem = self.problem
        p1 = problem.init_nodes
        p2 = problem.final_nodes

        # Nodes that need z variables
        if not self.collapse:
            z_n = set(problem.modify_nodes).union(problem.final_only_nodes)
        else:
            z_n = problem.modify_nodes

        # Z variables to encode choice
        Z = ['z' + str(n) for n in z_n]
        Z_id = {n : z for z,n in enumerate(z_n)}
        bdd.declare(*Z)

        trans = bdd.false
        for n, ni in n_map.items():
            # Last node of path does not have any successor
            if n == p1[-1] or n == p2[-1]:
                continue

            # If n on both paths and change routing, we need to use z variables
            if n in problem.modify_nodes:
                p1_succ = problem.init_succ[n]
                p2_succ = problem.final_succ[n]

                to_1 = n_map[p1_succ[0]] 
                to_2 = n_map[p2_succ[0]]
                if problem.is_weighted:
                    c1 = problem.top[n][p1_succ[0]][p1_succ[1]]['weight']
                    c1 = Cost(self.cost_size,c1).to_BDD(self.C1, self)

                    c2 = problem.top[n][p2_succ[0]][p2_succ[1]]['weight']   
                    c2 = Cost(self.cost_size,c2).to_BDD(self.C1, self)

                    to_add = (S[ni] & bdd.var(Z[Z_id[n]]) & c1 & T[to_1]) | (S[ni] & (~bdd.var(Z[Z_id[n]])) & c2 & T[to_2])
                else:
                    to_add = (S[ni] & bdd.var(Z[Z_id[n]]) & T[to_1]) | (S[ni] & (~bdd.var(Z[Z_id[n]])) & T[to_2])
                trans = trans | to_add

            # If n on p1 and does not change routing in p2, use p1 successor
            elif n in problem.init_only_nodes.union(problem.no_change_nodes):
                succ = problem.init_succ[n]
                to = n_map[succ[0]]

                if problem.is_weighted:
                    c = problem.top[n][succ[0]][succ[1]]['weight']
                    c = Cost(self.cost_size,c).to_BDD(self.C1, self)
                    to_add = (S[ni] & c & T[to])
                else:
                    to_add = (S[ni] & T[to])
                trans = trans | to_add

            # If n only on p2, use z variable to enable transition
            elif n in problem.final_only_nodes:
                succ = problem.final_succ[n]
                to = n_map[succ[0]]

                if problem.is_weighted:
                    c = problem.top[n][succ[0]][succ[1]]['weight']
                    c = Cost(self.cost_size,c).to_BDD(self.C1, self)
                    if not self.collapse:
                        to_add = (S[ni] & c & (~bdd.var(Z[Z_id[n]])) & T[to])
                    else:
                        to_add = (S[ni] & c & T[to])
                else:
                    if not self.collapse:
                        to_add = (S[ni] & (~bdd.var(Z[Z_id[n]])) & T[to])
                    else:
                        to_add = (S[ni] & T[to])
                trans = trans | to_add    

        self.Z = Z
        self.trans = trans

    def gen_transitions_unrestricted(self):
        assert self.is_weighted == False
        self.gen_edges()

        S = self.S
        T = self.T
        E = self.E
        bdd = self.bdd
        n_map = self.n_map
        problem = self.problem
        p1 = problem.init_nodes
        p2 = problem.final_nodes

        trans = bdd.false
        # Loop over all nodes in self.E
        for n in problem.top.nodes():
            if n == p1[-1] or n == p2[-1]:
                continue

            ni = self.n_map[n]

            if n in self.E:
                # Loop over all successor nodes
                for succ in self.E[n]:
                    # Loop over each concrete edge
                    for e in self.E[n][succ]:
                        trans = trans | (S[ni] & (E[n][succ][e]) & T[n_map[succ]])

            else:
                # Make transition to single successor
                succ = problem.init_succ[n]
                to = n_map[succ[0]]
                trans = trans | (S[ni] & T[to])
     
        self.trans = trans

    def gen_config_transitions(self):
        if self.is_restricted:
            self.gen_config_transitions_restricted()
        else:
            self.gen_config_transitions_unrestricted()

    def gen_config_transitions_restricted(self):
        bdd = self.bdd
        Z = self.Z
        ZZ = [z.replace('z','zz') for z in self.Z]

        bdd.declare(*ZZ)
    
        self.ZZ = ZZ
        # An update is where Z and ZZ values agree except at one index (p), where zz is set to false and z is true
        res = bdd.false
        for p in range(len(Z)):
            z_add = bdd.true
            for i in range(len(Z)):
                zi_add = bdd.var(Z[i]).equiv(bdd.var(ZZ[i]))
                if i == p:
                    zi_add = bdd.var(Z[i]).equiv(bdd.true) & bdd.var(ZZ[i]).equiv(bdd.false)
                z_add = z_add & zi_add
            res = res | z_add
        self.CTrans = res

    def gen_config_transitions_unrestricted(self):
        self.ZZ_map = dict()
        self.ZZ = []
        bdd = self.bdd
        # An update is where, for one switch, an edge was changed
        res = bdd.false

        # Get all edges
        edges_bdd = dict()
        single_edge = dict()

        for n in self.E:
            edges_bdd[n] = []

            # Detect single edge nodes
            single_edge[n] = False
            if len(self.E[n]) == 1:
                succ = list(self.E[n].keys())[0]
                if len(self.E[n][succ]) == 1:
                    single_edge[n] = True

            # get edge BDDs
            for succ in self.E[n]:
                for e in self.E[n][succ]:
                    config = self.BDD_to_config(self.E[n][succ][e])
                    values = list(config.values())
                    edges_bdd[n].append(self.E[n][succ][e])

            # Declare ZZ
            zz = [z.replace('z','zz') for z in self.Z_map[n]]
            self.ZZ_map[n] = zz
            bdd.declare(*zz)
            self.ZZ += zz

        # Disjunction over all nodes
        for n in self.Z_map:
            n_res = bdd.true
            for nn in self.Z_map:
                nn_res = bdd.false

                z_to_zz = {str(z) : str(z).replace('z','zz') for z in self.Z_map[nn]}

                # Create transitions betweeen different edges
                for e_start in edges_bdd[nn]:
                    e_res = bdd.false
                    for e_succ in edges_bdd[nn]:
                        # If same node, e_start and e_succ same should not be included
                        if n == nn:
                            if e_start == e_succ:
                                if single_edge[nn]:
                                    # Single edge can be turned on and off
                                    e_res = e_res | (e_start & bdd.let(z_to_zz, ~e_succ))
                                    e_res = e_res | (~e_start & bdd.let(z_to_zz, e_succ))
                                else:
                                    continue
                            else:
                                e_res = e_res | (e_start & bdd.let(z_to_zz, e_succ))
                        else:
                            # If same node, e_start & e_succ must be included to say that no change is made
                            if e_start == e_succ:
                                e_res = e_res | (e_start & bdd.let(z_to_zz, e_succ))

                                # If single edge, its negation is also a valid config.
                                if single_edge[nn]:
                                    e_res = e_res | (~e_start & bdd.let(z_to_zz, ~e_succ))
                            else:
                                continue  
                    nn_res = nn_res | e_res
                n_res = n_res & nn_res          
            res = res | n_res
        self.CTrans = res

    def get_all_symbolic(self, inv):
        bdd = self.bdd
        sol = bdd.true   

        _, goal_bdd = self.get_start_and_goal()

        reach = goal_bdd & inv
        reach_old = None

        res = []

        z_to_zz = {str(z) : str(z).replace('z','zz') for z in self.Z}
        zz_to_z = {str(zz) : str(zz).replace('zz','z') for zz in self.ZZ}
        swap_z = {**z_to_zz, **zz_to_z}

        while reach != reach_old: 
            res.append(reach)
            reach_old = reach
            s1 = self.bdd.let(swap_z, reach_old)
            s2 = self.bdd.exist(self.Z, s1)
            s3 = (self.CTrans & s2)
            reach = inv & (reach_old | s3)

        return res

    def get_some(self, sol=None, inv=None):
        if self.is_restricted:
            return self.get_some_restricted(sol,inv)
        else:
            return self.get_some_unrestricted(sol,inv)

    def get_some_restricted(self, sol=None, inv=None):
        assert self.is_restricted
        res = []

        if sol is None:
            if inv is None:
                raise ValueError("Must provide inv to generate solutions if sol not given")
            else:
                sol = self.get_all_symbolic(inv)

        # Any solution must update all changing nodes
        if len(sol) <= len(self.Z):
            print("Solution shorter than needed...")
            return False

        start_bdd, goal_bdd = self.get_start_and_goal()
        start = list(self.bdd.pick_iter(start_bdd))[0]
        end = list(self.bdd.pick_iter(goal_bdd))[0]

        #  Assumes each switch is updated once...
        for i in range(len(sol)-1,0,-1): 
            found_valid_succ = False
            if self.is_weighted:
                sol[i] = self.bdd.exist(self.C1, sol[i])
            sol_start = and_exists(sol[i], start_bdd, self.Z)
            for z in start: 
                if start[z]:
                    succ = start.copy()
                    succ[z] = False

                    succ_map = {z.replace('z','zz') : val for z, val in succ.items()}
                    succ_valid = self.bdd.let(succ_map, sol_start)

                    if succ_valid == self.bdd.true:
                        edge = int(z.strip('z'))
                        res.append(edge)
                        found_valid_succ = True
                        start = succ
                        start_bdd = self.config_to_BDD(start)
                        break

            if found_valid_succ == False:
                print("Did not find valid successor")
                return False

            # Goal found, can break (avoids loops)
            if start == end:
                break
        return res

    def get_some_unrestricted(self, sol=None, inv=None):
        res = []

        if sol is None:
            if inv is None:
                raise ValueError("Must provide inv to generate solutions if sol not given")
            else:
                sol = self.get_all_symbolic(inv)

        start_bdd, goal_bdd = self.get_start_and_goal()

        goal_config = self.BDD_to_config(goal_bdd)

        seq = []
        # By doing it like this, we will not be able to produce solutions that flip back and forth
        for i in range(len(sol)-1,0,-1):
            start_config = self.BDD_to_config(start_bdd)
            succs = and_exists(sol[i], start_bdd, self.Z)

            all_succ = list(self.bdd.pick_iter(succs))
            some_succ = all_succ[0] # We just pick the first
            some_succ = {z.replace('zz','z') : val for z, val in some_succ.items()}

            found = False
            for n in self.E:
                if found:
                    break
                for succ in self.E[n]:
                    if found:
                        break
                    for e in self.E[n][succ]:
                        if found:
                            break
                        e_config = self.BDD_to_config(self.E[n][succ][e]) 

                        start_ls = set(start_config.items())
                        some_succ_ls = set(some_succ.items())
                        e_config = set(e_config.items())

                        if e_config.issubset(some_succ_ls) and (not e_config.issubset(start_ls)):
                            seq.append('{}->{}:{}'.format(n,succ,e))
                            found = True
                            break

            start_bdd = self.config_to_BDD(some_succ)

            if start_bdd == goal_bdd:
                print("Start is equal to goal")
                return seq
            elif start_bdd & goal_bdd != self.bdd.false:
                print("Start is consistent with goal")
                return seq

        return False
        
    def get_optimal(self, inv, get_sequence, op_req=None):
        #assert self.is_restricted
        
        #minimum cost is the least cost you need to make sure that any intermediate stays below...
        #maximum of intermediate configs is below the optimal cost...
        all_sol = self.get_all_symbolic(inv=inv)

        if op_req != None:
            op_req_bdd = op_req.compile_seq(self)

            for i in range(len(all_sol)):
                all_sol[i] = all_sol[i] & op_req_bdd

        start = {z : True for z in self.Z}

        # No solution for start config -> -1 cost
        if self.bdd.let(start, all_sol[-1]) == self.bdd.false:
            return Cost(self.cost_size, -1)

        c1_to_c2 = {self.C1[c] : self.C2[c] for c in range(len(self.C1))}
        leq_check = Cost.LEQ(self.C1, self.C2, self)
        zz_to_z = {str(zz) : str(zz).replace('zz','z') for zz in self.ZZ}

        config_sequence = [start]
        opt_cost = -1

        if get_sequence:
            r = range(len(self.Z),0,-1)
        else:
            r = range(len(self.Z),len(self.Z)+1)

        for i in r:
            # Finds optimal values for all configs
            s1 = self.bdd.let(c1_to_c2, all_sol[i]).implies(leq_check)
            opt = all_sol[i] & self.bdd.forall(self.C2, s1)

            # Find optimal values for start config for any successor
            best_costs_succ = self.bdd.let(start, opt)

            # Quantify away successors
            best_costs = self.bdd.exist(self.ZZ, best_costs_succ)

            # Find the best cost
            s1 = self.bdd.let(c1_to_c2, best_costs).implies(leq_check)

            # Quantify away C2 vars
            opt_start = best_costs & self.bdd.forall(self.C2, s1)

            if i == len(self.Z):
                opt_cost = Cost.BDD_to_cost(self, self.C1, opt_start)
            
            start = self.bdd.exist(self.C1, best_costs_succ & opt_start)  
            start = self.BDD_to_config(self.bdd.let(zz_to_z, start))    
 
            if get_sequence:
                config_sequence.append(start)
        
        up_seq = None
        if get_sequence:
            seen = set()
            up_seq = []
            for config in config_sequence[1:]:
                for n in config:
                    if config[n] == False and n not in seen:
                        up_seq.append(int(n.strip('z')))
                        seen.add(n)

        return opt_cost, up_seq

    def is_solution(self, seq, sol=None, inv=None):
        assert self.is_restricted
        if sol is None:
            if inv is None:
                raise ValueError("Must provide inv to generate solutions if sol not given")
            else:
                sol = self.get_all_symbolic(inv)
        
        assert len(seq) == len(self.Z) 
        assert len(sol) ==  len(self.Z) + 1
    
        start = {z: True for z in self.Z}
        start_bdd = self.config_to_BDD(start)

        found_valid_succ = False
        #  Assumes each switch is updated once...
        for i in range(len(self.Z),0,-1): 
            sol_start = and_exists(sol[i], start_bdd, self.Z)
            succ = self.get_config_successors(start)
            
            succ = start.copy()
            curr_z = 'z' + str(seq[len(seq)-i])

            succ[curr_z] = False
            succ_map = {'z' + str(z) : val for z, val in succ.items()}
            succ_valid = self.bdd.let(succ_map, sol_start)
 
            if succ_valid == self.bdd.true:
                start = succ
                start_bdd = self.config_to_BDD(start)
            else:
                return False
        return True
        
    def satcount(self, sol):
        if self.is_weighted:
            sol = self.bdd.exist(self.C1, sol)

        start_bdd, goal_bdd = self.get_start_and_goal()
        step_count = len(self.Z)

        sub_start = {z : z + 's0' for z in self.Z}
        sub_goal = {z : z + 's' + str(len(self.Z)) for z in self.Z}

        self.bdd.declare(*sub_start.values())
        self.bdd.declare(*sub_goal.values())

        start_step = self.bdd.let( sub_start, start_bdd)
        goal_step = self.bdd.let( sub_goal, goal_bdd)

        res = start_step & goal_step

        # Solutions only of length equal to number of Z vars
        for i in range(step_count):
            step_sub_z = {z : z + 's' + str(i) for z in self.Z}
            step_sub_zz = {zz : zz.replace('zz','z') + 's' + str(i+1) for zz in self.ZZ}
            step_sub = {**step_sub_z, **step_sub_zz}
            self.bdd.declare(*step_sub.values())

            step_i = self.bdd.let(step_sub, sol)
            res = res & step_i

        return self.bdd.count(res)

    def exists(self, inv):
        bdd = self.bdd
        sol = bdd.true

        start_bdd, goal_bdd = self.get_start_and_goal()
        
        reach = goal_bdd & inv
        reach_old = None

        z_to_zz = {str(z) : str(z).replace('z','zz') for z in self.Z}

        while reach != reach_old:
            reach_old = reach
            s1 = self.bdd.let(z_to_zz, reach_old)
            s3 = and_exists(self.CTrans, s1, self.ZZ)
            reach = inv & (reach_old | s3)

        s4 = start_bdd & inv
        reach = and_exists(reach, s4, self.Z)

        if reach == self.bdd.false:
            return False
        elif reach == self.bdd.true:
            return True
        else:
            raise ValueError("Exists non-Boolean value produced!")   

    def gen_init_end_V(self):
        bdd = self.bdd
        sol = self.bdd.true

        # V's must be true from beginning
        for v in self.V[0]:
            sol = sol & bdd.var(v)

        # V's must end up being false
        for v in self.V[len(self.Z)]:
            sol = sol & (~bdd.var(v))
        return sol

    def get_all_explicit(self, inv):
        bdd = self.bdd
        V = dict()
        for s in range(len(self.Z)+1):
            V[s] = ['v' + str(s+1) + "_" + z[1:] for z in self.Z]
            for v in V[s]:
                self.bdd.declare(v)
        self.V = V
        
        init = self.gen_init_end_V() 
        all_explicit = init & self.gen_safe_update(self.V, inv)
        
        solutions = list(bdd.pick_iter(all_explicit))

        sequences = []
        seen = set()
        for s in range(len(solutions)):
            seen = set()
            ls = []
            for it in range(2,len(self.V)+1,1):
                it_vals = { v: val for v, val in solutions[s].items() if v.startswith('v'+str(it))}
                it_vals_node_key = {int(v[v.index('_'):].strip('_')):val for v, val in it_vals.items()}

                for node, val in it_vals_node_key.items():
                    if val == False and (node not in seen):
                        ls.append(node)
                        seen.add(node)
            sequences.append(ls)
        
        return sequences

    def gen_safe_update(self, V, inv):
        bdd = self.bdd

        sol = bdd.true
        # Safety and update choice
        for i in range(len(V)):
            # Each intermediate must be safe
            m = {self.Z[z] : V[i][z] for z in range(len(self.Z))}
            sol = sol & bdd.let(m, inv)  
            # Choose which link to enable or modify
            if i < len(V)-1:
                z_to_v = {self.Z[z] : V[i][z] for z in range(len(self.Z))}
                zz_to_v = {"z" + self.Z[z] : V[i+1][z] for z in range(len(self.Z))}
                sub = bdd.let ({**z_to_v, **zz_to_v}, self.CTrans)
                sol = sol & sub
        return sol   
