from bddbase import BDDbase, Cost
from enum import Enum
from itertools import permutations
from property import Conjunction, CostBoundedReachability
from dd.cudd import BDD, dump
import pickle

class VerifyMethod(Enum):
    exists = 0
    allSymbolic = 1
    some = 2
    allExplicit = 3

class BooleanSolution:
    def __init__(self, base, ans):
        self.ans = ans
        self.base = base

    def __str__(self):
        return str(self.ans)

    def __eq__(self, other):
        return (isinstance(other, BooleanSolution) and self.ans == other.ans) \
               or isinstance(other, bool) and self.ans == other

class ExplicitSolution:
    def __init__(self, base, seq, prefix=set(), suffix=set()):
        self.prefix = prefix
        self.suffix = suffix
        self.seq = seq
        self.base = base

    def __str__(self):
        return str((self.prefix, self.seq, self.suffix))

    def __iter__(self):
        perm_pre = permutations(self.prefix)
        perm_suff = permutations(self.suffix)

        for pre in perm_pre:
            for suff in perm_suff: 
                yield ExplicitSolution(self.base, list(pre) + self.seq + list(suff))

class ExplicitSolutionSet:
    def __init__(self, base, prefix=set(), suffix=set()):
        self.solutions = set()
        self.prefix = prefix
        self.suffix = suffix
        self.base = base

    def __iter__(self):
        for s in self.solutions:
            yield s

    def __contains__(self, sol):
        for s in self.solutions:
            if isinstance(sol, list):
                if s.seq == sol:
                    return True
            else:
                if s.prefix == sol.prefix and \
                    s.seq == sol.seq and \
                    s.suffix == sol.suffix:
                    return True
                else:
                    # Below is the worst piece of code ever implemented
                    perm_pre_s = permutations(s.prefix)
                    for pre_s in perm_pre_s:
                        perm_pre_sol = permutations(sol.prefix)
                        for pre_sol in perm_pre_sol:
                            perm_suff_s = permutations(s.suffix)
                            for suff_s in perm_suff_s:
                                perm_suff_sol = permutations(sol.suffix)
                                for suff_sol in perm_suff_sol:
                                    if list(pre_s) + s.seq + list(suff_s) ==  list(pre_sol) + sol.seq + list(suff_sol):
                                        return True
        return False
    
    def __len__(self):
        return len(self.solutions)

    def __str__(self):
        res = ""
        for s in self.solutions:
            res = res + str(s) + "\n"
        return res
        
class SymbolicSolution:
    def __init__(self, base, sols, prefix=set(), suffix=set()):
        self.prefix = prefix
        self.suffix = suffix
        self.sols= sols
        self.base = base

    def get_some(self):
        return ExplicitSolution(self.base, self.base.get_some(sol=self.sols),prefix=self.prefix,suffix=self.suffix)

    def is_solution(self, sol):
        if isinstance(sol, list):
            # This only ensures that z-nodes are in correct relative order...
            return self.base.is_solution([n for n in sol if n not in self.prefix.union(self.suffix)], self.sols)
        else:
            return self.base.is_solution([n for n in sol.seq if n not in self.prefix.union(self.suffix)], self.sols)

    def is_empty(self):
        if self.base.is_restricted:
            return len(self.sols) < len(self.base.Z)
        else:
            return self.base.satcount(self.sols[-1]) == 0

    def count(self):
        return self.base.satcount(self.sols[-1])

    def __str__(self):
        if self.is_empty():
            return "empty"
        else:
            return "non-empty"

    def dump(self, filename):
        bdd = self.base.bdd

        # The below is a slight variant of cudd.pyx
        # dump method to make it work with CUDD BDD manager

        pickle_fname = '{s}.pickle'.format(s=filename)

        order = {var: bdd.level_of_var(var)
                for var in bdd.vars}
        d = dict(variable_order=order)

        with open(pickle_fname, 'wb') as f:
            pickle.dump(d, f, protocol=2)

        for s in range(len(self.sols)):
            self.base.bdd.dump(filename + "_{}.dddmp".format(s),roots=[self.sols[s]])
        
        # To make load work...
        self.base.bdd.dump(filename + ".dddmp",roots=[self.sols[-1]])

class OptimalSolution:
    def __init__(self, base, cost, seq,prefix=set(),suffix=set()):
        self.cost = cost
        self.base = base
        self.seq = seq
        self.prefix = prefix
        self.suffix = suffix

    def __str__(self):
        if self.seq == None:
            return str(self.cost) 
        else:
            return str((self.prefix, self.seq, self.suffix)) + " val: {}".format(self.cost)

    def __eq__(self, other):
        return isinstance(other, OptimalSolution) and \
               self.cost == other.cost and \
               self.seq == other.seq

def verify(problem, method=VerifyMethod.exists,collapse=False,bound=None,op_req=None): 
    # Hack for now
    problem.isWeighted = False

    base = BDDbase()
    base.generate(problem,collapse,bound=bound)

    if collapse:
        prefix = problem.final_only_nodes
    else:
        prefix = set()

    suffix = problem.init_only_nodes.union(problem.no_change_nodes) # Why is no_change here? For NS?

    if bound != None:
        inv = Conjunction(problem.prop, CostBoundedReachability(problem.init_nodes[-1], bound))
        inv = inv.verify(base, problem.init_nodes[0])
    else:
        inv = problem.prop.verify(base, problem.init_nodes[0])

    if method == VerifyMethod.exists:
        ans = base.exists(inv=inv)
        return BooleanSolution(base, ans)

    elif method == VerifyMethod.allSymbolic:
        sol = base.get_all_symbolic(inv=inv)   
        if op_req != None:
            op_req_bdd = op_req.compile_seq(base)

            for i in range(len(sol)):
                sol[i] = sol[i] & op_req_bdd

        return SymbolicSolution(base, sol, prefix=prefix, suffix=suffix)

    elif method == VerifyMethod.some:
        sol = base.get_all_symbolic(inv=inv) 

        if op_req != None:
            op_req_bdd = op_req.compile_seq(base)

            for i in range(len(sol)):
                sol[i] = sol[i] & op_req_bdd

        return SymbolicSolution(base, sol, prefix=prefix, suffix=suffix).get_some()

    elif method == VerifyMethod.allExplicit:
        sol = base.get_all_explicit(inv=inv)
        res = ExplicitSolutionSet(base, prefix=prefix, suffix=suffix)
        for s in sol:
            res.solutions.add(ExplicitSolution(base, s, prefix=prefix, suffix=suffix))
        return res

    else:
        raise ValueError("Unknown verification method supplied")

def get_optimal(problem, get_sequence, collapse=False, op_req=None):      
    base = BDDbase()
    base.generate(problem,collapse)

    if collapse:
        prefix = problem.final_only_nodes
    else:
        prefix = set()

    suffix = problem.init_only_nodes.union(problem.no_change_nodes) # noChange should not be here...

    cost_reach = Conjunction(problem.prop, CostBoundedReachability(problem.init_nodes[-1]))

    safe_cost = cost_reach
    inv = safe_cost.verify(base, problem.init_nodes[0])

    opt, seq = base.get_optimal(inv, get_sequence, op_req)

    return OptimalSolution(base, opt, seq, prefix, suffix)


