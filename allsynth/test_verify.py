import unittest
from verify import verify, VerifyMethod, ExplicitSolution, get_optimal
from bddbase import BDDbase
from property import *
from experiments import *
from problem import SynthesisProblem
import networkx as nx
from dd.autoref import BDD

class ReachTests(unittest.TestCase):

    def test_slides(self):
        p1 = [0,1,2,3,4]
        p2 = [0,1,3,2,4]

        p1ext = p1 + [5,6]
        p2ext = p2 + [6]

        prop = Conjunction(Reachability(2), Reachability(4))

        p = SynthesisProblem(p1, p2, prop)
        sol = verify(p, VerifyMethod.exists)
        self.assertEqual(sol, True)

        sol =  verify(p, VerifyMethod.allExplicit)
        expected = [2,3,1]
        base = sol.base
        self.assertEqual(len(sol),1)

        self.assertTrue(expected in sol)

        self.assertTrue(base.is_solution(expected, inv=prop.verify(base, 1)))

        expected = verify(p,VerifyMethod.some)

        self.assertTrue(expected in sol)

        p = SynthesisProblem(p1ext, p2ext, Reachability(6))
        sol_ext = verify(p, VerifyMethod.allExplicit)
        expected_ext = 12

        self.assertEqual(len(sol_ext),expected_ext)

        
    def test_disjoint(self):
        p1 = [1,2,4]
        p2 = [1,2,3,4]

        prop = Reachability(4)

        p = SynthesisProblem(p1,p2,prop)
        sol = verify(p, VerifyMethod.exists)
        self.assertEqual(sol.ans, True)

        sol = verify(p, VerifyMethod.allExplicit)
        expected = [3,2]

        base = sol.base
        self.assertTrue(expected in sol)

        self.assertTrue(base.is_solution(expected, inv=prop.verify(base, 1)))

        expected = verify(p, VerifyMethod.some)
        self.assertTrue(expected in sol)

    def test_Nate_Foster_rb_reach(self):
        p1 = [0,4,8,6,2]
        p2 = [0,5,8,7,2]
        prop = Reachability(2)

        p = SynthesisProblem(p1,p2,prop)
        sol = verify(p, VerifyMethod.exists)
        self.assertEqual(sol, True)

        sol_explicit = verify(p, VerifyMethod.allExplicit)
        expected = 6

        self.assertEqual(expected, len(sol_explicit))

        expected = verify(p, VerifyMethod.some)

        self.assertTrue(expected in sol_explicit)

        sol_2 = verify(p, VerifyMethod.some,collapse=True)

        for s in sol_2:
            self.assertTrue(s in sol_explicit)

    def test_Nate_Foster_rb_wp(self):
        p1 = [0,4,8,6,2]
        p2 = [0,5,8,7,2]

        reachEnd = Reachability(2)
        visit_wp1 = Reachability(5)
        visit_wp2 = Reachability(6)

        prop = Conjunction(reachEnd, Disjunction(visit_wp1, visit_wp2))

        p = SynthesisProblem(p1,p2,prop)
        sol = verify(p, VerifyMethod.exists)
        self.assertEqual(sol.ans, True)

        sol = verify(p, VerifyMethod.allExplicit)
        expected = 3

        self.assertEqual(len(sol), expected)

        expected = verify(p, VerifyMethod.some)
        self.assertTrue(expected in sol)
        
    # Palmetto! Toccoa Greenwood
    def test_palmetto_1(self):
        p1 = [33, 31, 26, 25]
        p2 = [33, 31, 21, 11, 13, 12, 26, 25]


        prop = Reachability(25)

        p = SynthesisProblem(p1,p2,prop)

        sol = verify(p, VerifyMethod.exists)
        self.assertEqual(sol.ans, True)

        sol= verify(p, VerifyMethod.allExplicit)

        expected = 24
        self.assertEqual(len(sol), expected)  

        expected = verify(p, VerifyMethod.some)
        self.assertTrue(expected in sol)    
      

class ConFluentTests(unittest.TestCase):
    def test_way_noloop(self):
        expected = [False, True, True]
        cases = [1,2,5,10]

        for i in range(len(cases)):
            p1, p2 = gen_confluent(cases[i])
            wp_prop = WayPoint(2,p1[-1])
            lf_prop = LoopFreedom()
            props = [Conjunction(wp_prop, lf_prop), wp_prop, lf_prop]

            for j in range(len(props)):
                p = SynthesisProblem(p1,p2,prop=props[j])
                sol = verify(p,VerifyMethod.exists)
                self.assertEqual(sol.ans, expected[j])

                sol2 = verify(p, VerifyMethod.allSymbolic)
                self.assertEqual(not sol2.is_empty(), expected[j])

class DiaSeparateTests(unittest.TestCase):

    def test_all_issolution_collapse_true(self):
        for i in range(20,300,20):
            p1, p2 = gen_diamondSeparateWP(i)

            src = p1[0]
            dst = p1[-1]
            prop = Reachability(dst)

            p = SynthesisProblem(p1,p2,prop)
            sol_expl = verify(p,VerifyMethod.allExplicit,True) 
            sol_sym = verify(p,VerifyMethod.allSymbolic,True) 

            stop = 1000
            n = 0
            for s in sol_expl:
                for s_concrete in s:
                    if n == stop:
                        break
                    else:
                        self.assertTrue(sol_sym.is_solution(s_concrete))
                        n = n + 1

    def test_all_issolution_collapse_false(self):
        for i in range(5,10,1):
            p1, p2 = gen_diamondSeparateWP(i)

            src = p1[0]
            dst = p1[-1]
            prop = Reachability(dst)

            p = SynthesisProblem(p1,p2,prop)
            sol_expl = verify(p,VerifyMethod.allExplicit,False) 
            sol_sym = verify(p,VerifyMethod.allSymbolic,False) 

            stop = 500
            n = 0
            for s in sol_expl:
                for s_concrete in s:
                    if n == stop:
                        break
                    else:
                        self.assertTrue(sol_sym.is_solution(s_concrete))
                        n = n + 1

    def test_zigzag(self):
        p1, p2 = gen_zigzag(10)

        prop = Reachability(p1[-1])
        p = SynthesisProblem(p1,p2,prop)
        
        some_sol = [10, 0, 11, 1, 12, 2, 13, 3, 14, 4, 15, 5, 16, 6, 17, 7, 18, 8, 9]
        sol_sym = verify(p, VerifyMethod.allSymbolic, False)

        base = BDDbase()
        base.generate(p)

        sol_sym_inner = base.get_all_symbolic(p.prop.verify(base, p1[0]))
        some_sol_gen = base.get_some(sol_sym_inner)
        
        critical = [n for n in some_sol if n not in sol_sym.prefix.union(sol_sym.suffix)]


        self.assertTrue(base.is_solution(critical, sol_sym_inner))
        self.assertTrue(base.is_solution(some_sol_gen, sol_sym_inner))
        self.assertTrue(sol_sym.is_solution(some_sol))

class OptimiziationTests(unittest.TestCase):

    def test_dia_shared_reach(self):
        top = nx.MultiDiGraph()

        p1 = [(1,2, {"weight" : 1}), (2,3, {"weight" : 3})]
        p2 = [(1,2, {"weight" : 4}), (2,3, {"weight" : 1})]
        top.add_edges_from(p1)
        top.add_edges_from(p2)

        prop = Reachability(3)

        p = SynthesisProblem([(n,m,0) for n,m,w in p1], [(n,m,1) for n,m,w in p2], prop, top=top)
   
        opt1 = get_optimal(p, True, collapse=False)
        #opt2 = get_optimal(p, True, collapse=True)

        self.assertEqual(opt1.cost.value, 5)
        #self.assertEqual(opt2.cost.value, 5)

    def test_dia_Niif_reach(self):
        top = nx.MultiDiGraph()

        p1 = [(32, 11, {"weight" : 1}),
            (11, 27, {"weight" : 1}),
            (27, 15, {"weight" : 1}),
            (15, 14, {"weight" : 1})]

        p2 = [(32, 23, {"weight" : 1}),
            (23, 16, {"weight" : 1}),
            (16, 13, {"weight" : 1}),
            (13, 14, {"weight" : 1})]

        top.add_edges_from(p1)
        top.add_edges_from(p2)

        prop = Reachability(14)

        p1_path = [(n,m,0) for n,m,w in p1]
        p2_path = [(n,m,0) for n,m,w in p2]
        p = SynthesisProblem(p1_path, p2_path, prop, top=top)

        opt1 = get_optimal(p, False)
        opt2 = get_optimal(p, True)

        self.assertEqual(opt1.cost.value, 4)
        self.assertEqual(opt2.cost.value, 4)

class UnrestrictedTests(unittest.TestCase):
    def test_unsat(self):
        expected = [True]
        cases = [1]

        p1, p2 = gen_confluent(1)
        wp_prop = WayPoint(2,p1[-1])
        lf_prop = LoopFreedom()
        #props = [Conjunction(wp_prop, lf_prop)]#, wp_prop, lf_prop]

        print("============================")
        p = SynthesisProblem(p1,p2,prop=Conjunction(wp_prop, lf_prop),restricted=False)

        p.top.add_edges_from([(0,2,0)])

        sol = verify(p,VerifyMethod.some)
        sol_allsym = verify(p,VerifyMethod.allSymbolic)

        self.assertEqual(sol_allsym.count(), 1)

        #for ss in sol.base.bdd.pick_iter(sol.sols[-1]):
        #    print(ss)
        print(sol)

    def dtest_dia_opt_multi(self):
        top = nx.MultiDiGraph()

        p1 = [(1,2,0), (2,3,0), (3,4,0), (4,6,0)]
        p2 = [(1,2,1), (2,3,1), (3,4,0), (4,6,0)]
        top.add_edges_from(p1)
        top.add_edges_from(p2)

        prop = Reachability(6)

        p = SynthesisProblem(p1,p2, prop, restricted=False, top=top)
   
        base = BDDbase()
        base.generate(p)

        _,_ = base.get_start_and_goal()

        for n in base.E:
            for succ in base.E[n]:
                for e in base.E[n][succ]:
                    for s in base.bdd.pick_iter(base.E[n][succ][e]):
                        print(s)


        #sol = verify(p, VerifyMethod.some, collapse=False)
        #print(base.Z)
        #print(sol)
        #for s in sol.base.bdd.pick_iter(sol.sols[-1]):
        #    print(s)

    def dtest_figure_stuff(self):
        top = nx.MultiDiGraph()

        p1 = [(1,2,0), (2,3,0), (3,4,0), (4,6,0)]
        p2 = [(1,2,1), (2,3,1), (3,4,0), (4,6,0)]


        top.add_edges_from(p1)
        top.add_edges_from(p2)

        extra = [(1,7,0), (7,6,0)]
        top.add_edges_from(extra)

        prop = Reachability(6)

        p = SynthesisProblem(p1,p2, prop, restricted=False, top=top)
   
        base = BDDbase()
        base.generate(p)

        _,_ = base.get_start_and_goal()

        for n in base.E:
            for succ in base.E[n]:
                for e in base.E[n][succ]:
                    for s in base.bdd.pick_iter(base.E[n][succ][e]):
                        print(s)


        sol = verify(p, VerifyMethod.allSymbolic, collapse=False)
        #print(base.Z)
        #print(sol)
        #print("Solution")
        #for s in sol.base.bdd.pick_iter(sol.sols[-1]):
        #    print(s)

    def dtest_figure_2(self):

        p1 = ['s','v1','v2','d']
        p2 = ['s','v2','v1','d']

        p1 = [1,2,3,4]
        p2 = [1,3,2,4]

        prop = Reachability(4)

        wp = WayPoint(3,4)

        p = SynthesisProblem(p1,p2,prop)

        base = BDDbase()
        base.generate(p)

        inv = prop.verify(base, 1)

        inv_wp = wp.verify(base, 1)

        inv_conj = Conjunction(prop, wp).verify(base,1)

        #Print states
        for s in p1:
            print("State {}".format(s))
            print(list(base.bdd.pick_iter(base.S[base.n_map[s]])))

        # Kim order
        kim_order = {"x1":0, "x2": 1, "z1": 2, "z2": 3, "z3": 4, "y1": 5, "y2": 6, "zz1":7, "zz2":8, "zz3":9}
        start = {z : True for z in base.Z}

        # Reach
        print("Reach expr")
        print(base.bdd.to_expr(inv))
        for sol in base.bdd.pick_iter(inv):
            print(sol)
        print("REACH SOL")
        sol_prop = base.get_all_symbolic(inv=inv) 

        #start = {z : True for z in base.Z}
        #sol_start = base.bdd.let(start, sol[-1])
        print(base.bdd.to_expr(sol_prop[-1]))
        for sol in base.bdd.pick_iter(sol_prop[-1]):
            print(sol)
        base.bdd.dump("solreach.svg", roots=[sol_prop[-1]])

        # Reach
        print("WP expr")
        print(base.bdd.to_expr(inv_wp))
        for sol in base.bdd.pick_iter(inv_wp):
            print(sol)
        print("WP SOL")
        sol_prop = base.get_all_symbolic(inv=inv_wp) 

        #start = {z : True for z in base.Z}
        #sol_start = base.bdd.let(start, sol[-1])
        print(base.bdd.to_expr(sol_prop[-1]))
        for sol in base.bdd.pick_iter(sol_prop[-1]):
            print(sol)
        base.bdd.dump("solwp.svg", roots=[sol_prop[-1]])

        # Reach
        print("WP&Reach expr")
        print(base.bdd.to_expr(inv_conj))
        for sol in base.bdd.pick_iter(inv_conj):
            print(sol)
        print("WP&Reach SOL")
        sol_prop = base.get_all_symbolic(inv=inv_conj) 

        #start = {z : True for z in base.Z}
        #sol_start = base.bdd.let(start, sol[-1])
        print(base.bdd.to_expr(sol_prop[-1]))
        for sol in base.bdd.pick_iter(sol_prop[-1]):
            print(sorted(sol.items()))
        base.bdd.dump("solconj.svg", roots=[sol_prop[-1]])

if __name__ == '__main__':
    unittest.main()