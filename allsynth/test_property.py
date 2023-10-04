import unittest
import networkx as nx
from bddbase import BDDbase
from cost import Cost
from property import *
from problem import SynthesisProblem


class PropertyTests(unittest.TestCase):

    def test_noloop(self):
        p1 = [1,2,3,4]
        p2 = [1,5,6,4]

        p = SynthesisProblem(p1, p2, None)

        base = BDDbase()
        base.generate(p)

        l = LoopFreedom().verify(base,1)

        self.assertTrue(l == base.bdd.true)
    
    def test_loop(self):
        p1 = [1,2,3,4,5]
        p2 = [1,2,4,3,5]

        base = BDDbase()

        p = SynthesisProblem(p1,p2, None)
        base.generate(p)

        l = LoopFreedom().verify(base, 1)

        # z3: True, z4: False is not one of the loop-free configs
        res = base.bdd.let({'z3':base.bdd.true, 'z4': base.bdd.false}, l)

        self.assertTrue(res == base.bdd.false)

    def test_until_reach(self):
        p1 = [1,2,3,4]
        p2 = [1,3,2,4]

        base = BDDbase()

        p = SynthesisProblem(p1,p2,None)
        base.generate(p)

        r = Until(TTrue(), 4).verify(base, 1)

        res = base.bdd.let({'z2':base.bdd.false, 'z3': base.bdd.true}, r)

        self.assertTrue(res == base.bdd.true)

        reach = Reachability(4).verify(base, 1)

        self.assertTrue(reach == r)

    def test_service_chain(self):
        p1 = [0,1,2,3,4]
        p2 = [0,2,1,3,4]

        base = BDDbase()

        p = SynthesisProblem(p1,p2, None)
        base.generate(p)

        sc = ServiceChain([1,3], p1[-1])
        sc_verif = sc.verify(base, p1[0])

        res_false = [[False, True, True], [False, False, True]]
        res_true = [[True, True, True], [True,False,False], [True, False, True],
                    [False, False, False], [False, True, False]]

        for r in res_false:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, sc_verif)
            self.assertTrue(actual == base.bdd.false)

        for r in res_true:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, sc_verif)
            self.assertTrue(actual == base.bdd.true)

        sc_verif_nosol = Conjunction(sc, Reachability(4)).verify(base, p1[0])

        res_false = [[False, True, True], [False, False, True]]
        res_true = [[True, True, True], [True,False,False], [True, False, True], [False, False, False]]

        for r in res_false:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, sc_verif)
            self.assertTrue(actual == base.bdd.false)

        for r in res_true:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, sc_verif)
            self.assertTrue(actual == base.bdd.true)

    def test_waypointing(self):
        p1 = [0,1,2,3,4]
        p2 = [0,3,2,1,4]

        base = BDDbase()

        p = SynthesisProblem(p1,p2, None)
        base.generate(p)

        wp = 2

        wp_prop =  WayPoint(wp,4).verify(base, 0)

        # z0,z1,z2,z3
        res_true = [[False, True, True, False], [False, False, True, False],
                    [True, True, True, True], [False, False, False, False]]

        res_false = [[False, False, False, True],
                      [False, True, False, True]]

        for r in res_true:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, wp_prop)
            self.assertTrue(actual == base.bdd.true)

        for r in res_false:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, wp_prop)
            self.assertTrue(actual == base.bdd.false)

    def test_reach_trivial_node_change(self):
        p1 = [0,1,2,3]
        p2 = [0,2,1,3]
        base = BDDbase()


        p = SynthesisProblem(p1, p2, None)
        base.generate(p)

        reach = Reachability(3).verify(base, 0)

        res_true = [[False, False, False], [True, True, True], [True, False, True], [False, False, True]]
        res_false = [[True, True, False], [False, True, False]]

        for r in res_true:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, reach)
            self.assertTrue(actual == base.bdd.true)

        for r in res_false:
            d = {z:r[i] for i, z in enumerate(base.Z)}
            actual = base.bdd.let(d, reach)
            self.assertTrue(actual == base.bdd.false)

    def test_reach_cost_disjoint(self):
        top = nx.MultiGraph()

        p1 = [(1,2, {"weight" : 1}), (2,3, {"weight" : 2})]
        p2 = [(1,4, {"weight" : 1}), (4,3, {"weight" : 1})]
        top.add_edges_from(p1)
        top.add_edges_from(p2)

        prop = CostBoundedReachability(3)

        p = SynthesisProblem([(n,m,0) for n,m,w in p1], [(n,m,0) for n,m,w in p2], prop, top=top)

        base = BDDbase()
        base.generate(p)

        sol = prop.verify(base, 1)

        nums = [list(base.bdd.pick_iter(Cost(base.cost_size, i).to_BDD(base.C1, base)))[0] for i in range(6+1)]

        no_constrain = [{'z1' : True, 'z4': False}, {'z1': True, 'z4' : True}, {'z1': False, 'z4' : True}, {'z1': False, 'z4' : False}]

        p1_enabled = [{'z1' : True, 'z4': False}, {'z1': True, 'z4' : True}]
        p2_enabled = {'z1': False, 'z4': False}

        # zero-one not possible under any z assignment
        for n in range(2):
            for i in range(len(no_constrain)):
                actual = base.bdd.let({**nums[n], **no_constrain[i]}, sol)
                expected = base.bdd.false
                self.assertEqual(actual, expected)

        # if p1_enabled, 3-6 possible
        for n in range(3,6+1,1):
            for p in p1_enabled:
                actual = base.bdd.let({**nums[n], **p}, sol)
                expected = base.bdd.true
                self.assertEqual(actual, expected)

        # if p2_enabled, 2-6 possible
        for n in range(2,6+1,1):
            actual = base.bdd.let({**nums[n], **p2_enabled}, sol)
            expected = base.bdd.true
            self.assertEqual(actual, expected)

    def test_reach_cost_multi_edge(self):
        top = nx.MultiGraph()

        p1 = [(1,2, {"weight" : 1}), (2,3, {"weight" : 2})]
        p2 = [(1,2, {"weight" : 2}), (2,3, {"weight" : 1})]
        top.add_edges_from(p1)
        top.add_edges_from(p2)

        prop = CostBoundedReachability(3)

        p = SynthesisProblem([(n,m,0) for n,m,w in p1], [(n,m,1) for n,m,w in p2], prop, top=top)

        base = BDDbase()
        base.generate(p)

        sol = prop.verify(base, 1)

        nums = [list(base.bdd.pick_iter(Cost(base.cost_size, i).to_BDD(base.C1, base)))[0] for i in range(3+1)]
        no_constrain = [{'z1' : True, 'z2': False}, {'z1': True, 'z2' : True}, {'z1': False, 'z2' : True}, {'z1': False, 'z2' : False}]

        one_config = {'z1' : True, 'z2': True}
    
        p2_enabled = {'z1': False, 'z4': False}

    def test_reach_weighted_model(self):
        top = nx.MultiGraph()

        p1 = [(1,2, {"weight" : 1}), (2,3, {"weight" : 2})]
        p2 = [(1,2, {"weight" : 2}), (2,3, {"weight" : 1})]
        top.add_edges_from(p1)
        top.add_edges_from(p2)

        prop = Reachability(3)

        p = SynthesisProblem([(n,m,0) for n,m,w in p1], [(n,m,1) for n,m,w in p2], prop, top=top)

        base = BDDbase()
        base.generate(p)

        sol = prop.verify(base, 1) 

        self.assertEqual(sol, base.bdd.true)

if __name__ == '__main__':
    unittest.main()