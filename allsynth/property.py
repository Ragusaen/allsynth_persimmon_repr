from dd.cudd import and_exists
from cost import Cost
import sys
sys.setrecursionlimit(10000)

class Property:
    def compile(self, base):
        pass

    def compile_seq(self, base):
        pass

    def verify(self, base, node):
        c = self.compile(base)

        n = base.n_map[node]
        n_bdd = base.S[n]

        return and_exists(c, n_bdd, base.X) 

    def get(self, prop):
        if isinstance(prop, int) or isinstance(prop, str):
            return SwitchID(prop)
        else:
            return prop

    def get_conjunction(prop1, prop2, p1, p2):
        return Conjunction(prop1(p1,p2), prop2(p1,p2))

    @staticmethod
    def get_servicechain(k, p1, p2):
        shared_nodes = [n for n in p1 if n in p2]
        wps = []

        n = 0
        for n in range(len(shared_nodes)):
            if n % k == 0 and n != 0:
                wps.append(shared_nodes[n])

        return ServiceChain(wps, p1[-1])
    
    @staticmethod
    def get_reachability(p1,p2):
        return Reachability(p1[-1])

    @staticmethod
    def get_noloop(p1,p2):
        return LoopFreedom()

    @staticmethod
    def get_waypoint_every(k, p1, p2):
        shared_nodes = [n for n in p1 if n in p2]

        wp_found = False
        for n in range(len(shared_nodes)):
            if n % k == 0 and n != 0:
                if wp_found == False:
                    prop = WayPoint(shared_nodes[n], p1[-1])
                else:
                    prop = Disjunction(prop, WayPoint(shared_nodes[n], p1[-1]))

                wp_found = True
        
        if wp_found:
            return prop
        else:
            return WayPoint(p1[-1],p1[-1])

    @staticmethod
    def get_waypoint_at(k, p1, p2):
        return WayPoint(k, p1[-1])

    @staticmethod
    def get_waypoint_only_initial_midway(p1, p2):
        p1_only = [n for n in p1 if n not in p2]
        middle = p1_only[int(len(p1_only)/2)]
        return WayPoint(middle, p1[-1])

    @staticmethod
    def get_sep_waypoint(p1, p2):
        p1_middle = int(len(p1) / 2)
        p2_middle = int(len(p2) / 2)

        wp1 = WayPoint(p1[p1_middle], p1[-1])
        wp2 = WayPoint(p2[p2_middle], p2[-1])

        return Disjunction(wp1, wp2)

    @staticmethod
    def get_sep_waypoint_every(k, p1, p2):
        wps = set()

        for n in range(len(p1)):
            if n % k == 0 and n != 0:
                wps.add(p1[n])
        
        for n in range(len(p2)):
            if n % k == 0 and n != 0:
                wps.add(p2[n])

        wps = list(wps)
        if len(wps) > 0:
            for wp in range(len(wps)):
                if wp == 0:
                    res = WayPoint(wps[wp],p1[-1])
                else:
                    res = Disjunction(res, WayPoint(wps[wp],p1[-1]))
        else:
            res = TTrue()

        return res

    @staticmethod 
    def get_cost_reach(p1, p2):
        return CostBoundedReachability(p1[-1])

class LoopFreedom(Property):

    def compile(self, base):
        l = base.bdd.true
        l_old = None
        x_to_y = {str(x) : str(x).replace('x','y') for x in base.X}
        while l != l_old:
            l_old = l
            l = and_exists(base.trans, base.bdd.let(x_to_y, l_old), base.Y)

            if base.is_weighted:
                l = base.bdd.exist(base.C1, l)

        return ~l 

    def compile_seq(self, base):
        l = base.bdd.true
        l_old = None
        z_to_zz = {str(z) : str(z).replace('z','zz') for z in base.Z}
        while l != l_old:
            l_old = l
            l = base.CTrans & base.bdd.let(z_to_zz, l_old)

            if base.is_weighted:
                l = base.bdd.exist(base.C1, l)

        return ~l 

    def __str__(self):
        return "NL"

class SwitchID(Property):
    def __init__(self, id):
        self.id = int(id)

    def compile(self, base):
        n = base.n_map[self.id]
        return base.S[n]

    def compile_seq(self, base):
        return ~base.bdd.var("z" + str(self.id))

    def __str__(self):
        return str(self.id)

    def __eq__(self, other):
        return (isinstance(other, SwitchID) and self.id == other.id) or \
               (isinstance(other, int) and self.id == other)

    def to_NetSynth(self):
        return "(port=in{}s)".format(self.id)

class Negation(Property):
    def __init__(self, prop):
        self.prop = self.get(prop)

    def compile(self, base):
        return ~self.prop.compile(base)

    def compile_seq(self, base):
        return ~self.prop.compile_seq(base)

    def __str__(self):
        return "~" + str(self.prop)

    def to_NetSynth(self):
        return "(!{})".format(self.prop.to_NetSynth())

class FFalse(Property):
    def __init__(self):
        pass

    def compile(self, base):
        return base.bdd.false
    
    def compile_seq(self, base):
        return base.bdd.false
            

    def __str__(self):
        return "FALSE"

    def to_NetSynth(self):
        return str(self)
    
class TTrue(Property):
    def __init__(self):
        pass

    def compile(self, base):
        return base.bdd.true
    
    def compile_seq(self, base):
        return base.bdd.true

    def __str__(self):
        return "TRUE"

    def to_NetSynth(self):
        return str(self)

    def to_FLIP(self):
        return []

class Disjunction(Property):
    def __init__(self, d1, d2):
        self.d1 = self.get(d1)
        self.d2 = self.get(d2)

    def compile(self, base):
        d1_bdd = self.d1.compile(base)
        d2_bdd = self.d2.compile(base)

        return d1_bdd | d2_bdd  

    def compile_seq(self, base):
        d1_bdd = self.d1.compile_seq(base)
        d2_bdd = self.d2.compile_seq(base)

        return d1_bdd | d2_bdd  

    def __str__(self):
        return "({} | {})".format(self.d1, self.d2) 

    def to_NetSynth(self):
        return "({} | {})".format(self.d1.to_NetSynth(), self.d2.to_NetSynth())

    def to_FLIP(self, p1, p2):
        d1_res = self.d1.to_FLIP(p1,p2)
        d2_res = self.d2.to_FLIP(p1,p2)

        res = d1_res + d2_res
        return res

    def to_persimmon(self):
        if isinstance(self.d1, WayPoint) and isinstance(self.d2, WayPoint):
            return '"MultiAlternativeWaypoint": {"waypoint": [' + f'{self.d1.wp},{self.d2.wp}' + ']}'
        elif isinstance(self.d1, Disjunction) and isinstance(self.d2, WayPoint):
            s = self.d1.to_persimmon()
            return s.replace(']', f',{self.d2.wp}]')

    def to_kaki(self):
        if isinstance(self.d1, WayPoint) and isinstance(self.d2, WayPoint):
            return '"DFA": {"initialState": 0, "finalStates": [' + f"{self.d1.wp},{self.d2.wp}" + '], "edges": [' + ','.join('{' + f'"from": 0, "to": {s}, "label": {s}' + '}' for s in [self.d1.wp, self.d2.wp]) + ']}'
        elif isinstance(self.d1, Disjunction) and isinstance(self.d2, WayPoint):
            s = self.d1.to_kaki()
            return s.replace('"finalStates": [', f'"finalStates": [{self.d2.wp},').replace('"edges": [', '"edges": [{' + f'"from": 0, "to": {self.d2.wp}, "label": {self.d2.wp}' + '},')

class Conjunction(Property):
    def __init__(self, c1, c2):
        self.c1 = self.get(c1)
        self.c2 = self.get(c2)

    def compile(self, base):
        c1_bdd = self.c1.compile(base)
        c2_bdd = self.c2.compile(base)

        return c1_bdd & c2_bdd

    def compile_seq(self, base):
        c1_bdd = self.c1.compile_seq(base)
        c2_bdd = self.c2.compile_seq(base)

        return c1_bdd & c2_bdd

    def __str__(self):
        return "({} & {})".format(self.c1, self.c2) 

    def to_NetSynth(self):
        return "({} & {})".format(self.c1.to_NetSynth(), self.c2.to_NetSynth())

    def to_persimmon(self):
        return f"{self.c1.to_persimmon()},{self.c2.to_persimmon()}"

    def to_kaki(self):
        return f"{self.c1.to_kaki()},{self.c2.to_kaki()}"

class Implication(Property):
    def __init__(self, p1, p2):
        self.p1 = self.get(p1)
        self.p2 = self.get(p2)
    
    def compile(self, base):
        p1_bdd = self.p1.compile(base)
        p2_bdd = self.p2.compile(base)

        return (~p1_bdd) | p2_bdd

    def compile_seq(self, base):
        p1_bdd = self.p1.compile_seq(base)
        p2_bdd = self.p2.compile_seq(base)

        return (~p1_bdd) | p2_bdd

    def __str__(self):
        return "({} -> {})".format(self.d1, self.d2)

    def to_NetSynth(self):
        return "({} -> {})".format(self.d1.to_NetSynth(), self.d2.to_NetSynth())

class WayPoint(Property):
    def __init__(self, wp, dst):
        self.wp = self.get(wp)
        self.dst = self.get(dst)
    
    def compile(self, base):
        dst_not_reach = Negation(Reachability(self.dst))
        wp_reach_noloop = Until(Negation(self.dst), Conjunction(self.wp, Reachability(self.dst)))
    
        return (dst_not_reach.compile(base)) | wp_reach_noloop.compile(base)

    def compile_seq(self, base):
        dst_not_reach = Negation(Reachability(self.dst))
        wp_reach_noloop = Until(Negation(self.dst), Conjunction(self.wp, Reachability(self.dst)))
    
        return (dst_not_reach.compile_seq(base)) | wp_reach_noloop.compile_seq(base)

    def __str__(self):
        return "WP({}-{})".format(self.wp, self.dst)

    def to_NetSynth(self):
        return "(port=in0s -> (!(port=out{}s) U ((port=in{}s) & (F (port=out{}s)))))".format(self.dst, self.wp, self.dst)

    def to_FLIP(self, p1, p2):
        p1_wp_index = p1.index(self.wp.id) if self.wp.id in p1 else None
        p2_wp_index = p2.index(self.wp.id) if self.wp.id in p2 else None

        res = []
        # If at beginning (index 0), no path property
        if p1_wp_index != None and p1_wp_index != 0:
            res.append([p1[p1_wp_index-1], p1[p1_wp_index]])
        if p2_wp_index != None and p2_wp_index != 0:
            res.append([p2[p2_wp_index-1], p2[p2_wp_index]])

        return res

    def to_persimmon(self):
        return '"Waypoint":{' + f'"finalNode": {self.dst},"waypoint": [{self.wp}]' + '}'

class ServiceChain(Property):
    def __init__(self, seq, dst):
        self.seq = seq
        self.dst = dst

    def unfold(self):
        if len(self.seq) == 0:
            return TTrue()
        else:
            # seq = w_i W'
            not_dst = Negation(self.dst)
            not_wk = TTrue()
            w_i = self.seq[0]

            for w_k in self.seq[1:]:
                not_wk = Conjunction(not_wk, Negation(w_k))

            tail = ServiceChain(self.seq[1:], self.dst).unfold()
            u = Until(Conjunction(not_dst, not_wk), 
                         Conjunction(w_i, tail))

            dst_not_reach = Negation(Reachability(self.dst))

            return Disjunction(dst_not_reach, u) # Is this correct?

    def compile(self, base):
        return self.unfold().compile(base)

    def compile_seq(self, base):
        return self.unfold().compile_seq(base)

    def __str__(self):
        return "Service({}-{})".format(self.seq, self.dst)

    def to_NetSynth(self):
        return self.unfold().to_NetSynth()

    def to_persimmon(self):
        return '"ServiceChain": {"waypoint": [' + ','.join(str(v) for v in self.seq) + ']}'

    def to_kaki(self):
        return '"DFA": {"initialState": 0, "finalStates": [' + str(len(self.seq)) + '], "edges": [' + ','.join('{' + f'"from": {i}, "to": {i+1}, "label": {s}' + '}' for i, s in enumerate(self.seq)) + ']}'

class Reachability(Property):
    def __init__(self, dst):
        self.dst = self.get(dst)

    def compile(self, base):
        reach = self.dst.compile(base)
        reach_old = None
        x_to_y = {str(x) : str(x).replace('x','y') for x in base.X}

        while reach != reach_old:
            reach_old = reach
            s1 = and_exists(base.trans, base.bdd.let(x_to_y, reach_old), base.Y)

            if base.is_weighted:
                s2 = base.bdd.exist(base.C1, s1)
                reach = reach_old | s2
            else:
                reach = reach_old | s1
        return reach   

    def compile_seq(self, base):
        reach = self.dst.compile_seq(base)
        reach_old = None
        z_to_zz = {str(z) : str(z).replace('z','zz') for z in base.Z}

        while reach != reach_old:
            reach_old = reach
            s1 = base.CTrans & base.bdd.let(z_to_zz, reach_old)

            if base.is_weighted:
                s2 = base.bdd.exist(base.C1, s1)
                reach = reach_old | s2
            else:
                reach = reach_old | s1

        return base.bdd.let(z_to_zz, reach)      

    def __str__(self):
        return "(Reach {})".format(self.dst)

    def to_NetSynth(self):
        return "(F {})".format(self.dst.to_NetSynth())

    def to_FLIP(self, p1, p2):
        p1_dest_link = [p1[-2], p1[-1]]
        p2_dest_link = [p2[-2], p1[-1]]
        return [p1_dest_link, p2_dest_link]

    def to_persimmon(self):
        return '"Reachability":{' + f'"startNode":-1,"finalNode":{self.dst}' + '}'

    def to_kaki(self):
        return self.to_persimmon()

class Until(Property):
    def __init__(self, phi_1, phi_2):
        self.phi_1 = self.get(phi_1)
        self.phi_2 = self.get(phi_2)

    def compile(self, base):
        sol = base.bdd.false
        sol_old = None

        phi_1_bdd = self.phi_1.compile(base)
        phi_2_bdd = self.phi_2.compile(base)

        x_to_y = {str(x) : str(x).replace('x','y') for x in base.X}

        while sol != sol_old:
            sol_old = sol
            s1 = and_exists(base.trans, base.bdd.let(x_to_y, sol_old), base.Y)
            s2 = phi_1_bdd & s1

            if base.is_weighted:
                s3 = base.bdd.exist(base.C1, s2)
                sol = phi_2_bdd | s3
            else:
                sol = phi_2_bdd | s2

        return sol

    def compile_seq(self, base):
        sol = base.bdd.false
        sol_old = None

        phi_1_bdd = self.phi_1.compile_seq(base)
        phi_2_bdd = self.phi_2.compile_seq(base)

        z_to_zz = {str(z) : str(z).replace('z','zz') for z in base.Z}

        while sol != sol_old:
            sol_old = sol
            s1 = and_exists(base.CTrans, base.bdd.let(z_to_zz, sol_old), base.ZZ)
            s2 = phi_1_bdd & s1

            if base.is_weighted:
                s3 = base.bdd.exist(base.C1, s2)
                sol = phi_2_bdd | s3
            else:
                sol = phi_2_bdd | s2

        return base.bdd.let(z_to_zz, sol)

    def __str__(self):
        return "({} U {})".format(self.phi_1, self.phi_2)

    def to_NetSynth(self):
        return "({} U {})".format(self.phi_1.to_NetSynth(), self.phi_2.to_NetSynth())  

class CostBoundedReachability(Property):
    def __init__(self, dst, c=None):
        self.dst = self.get(dst)
        self.bound = c

    def compile(self, base):
        reach = self.dst.compile(base)
        reach_old = None

        x_to_y = {str(x) : str(x).replace('x','y') for x in base.X}
        c1_to_c2 = {base.C1[c] : base.C2[c] for c in range(len(base.C1))}
        c1_to_c4 = {base.C1[c] : base.C4[c] for c in range(len(base.C4))}

        # Sum of C2 and C4 gives C3
        sum_check = Cost.sum_check(base.C2, base.C4, base.C3, base)

        # C3 is less than C1
        leq_check = Cost.LEQ(base.C3, base.C1, base)

        # Exist C3 such that sum_check and leq_check
        sum_leq_C3 = base.bdd.exist(base.C3, sum_check & leq_check)

        while reach != reach_old:
            reach_old = reach

            s_c = sum_leq_C3
            s_b = base.bdd.let({**x_to_y, **c1_to_c4}, reach)
            s_a = base.bdd.let(c1_to_c2, base.trans) 

            s1_ex = s_a & s_b & s_c

            s2_ex = base.bdd.exist(base.C2, s1_ex)
            s4_ex = base.bdd.exist(base.C4, s2_ex)
            s5_ex = base.bdd.exist(base.Y, s4_ex)

            reach = reach_old | s5_ex

        if self.bound != None:
            reach = reach & (Cost(len(base.C1), self.bound).to_BDD(base.C1, base))
        return reach

    def __str__(self):
        if self.bound == None:
            return "(Reach<=? {})".format(self.dst)
        else:
            return "(Reach<={} {})".format(self.bound, self.dst)

 
        