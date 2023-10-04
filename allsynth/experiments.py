import time
import os
from verify import verify, get_optimal, VerifyMethod
from netsynth import NetSynthSpec
from flip_run import FLIPSpec
from property import *
from bddbase import *
from problem import SynthesisProblem
from topology import *
from persimmon import PersimmonSpec
from kaki import KakiSpec

class VerifyConfig():
    def __init__(self, props, methods, collapse, tools, repeat, restrict, compute_count, bound):
        self.props = props
        self.methods = methods
        self.collapse = collapse
        self.tools = tools
        self.repeat = repeat
        self.restrict = restrict
        self.compute_count = compute_count
        self.bound = bound

class OptimizeConfig():
    def __init__(self, props, collapse, repeat, restrict, get_sequence):
        self.props = props
        self.collapse = collapse
        self.repeat = repeat
        self.restrict = restrict
        self.get_sequence = get_sequence

class Experiment():
    def __init__(self, name, problem):
        self.name = name
        self.problem = problem

    def __run__(self):
        pass

    def __str__(self):
        r = (self.name, self.problem.prop, len(self.problem.init_only_nodes), \
             len(self.problem.final_only_nodes), len(self.problem.no_change_nodes), len(self.problem.modify_nodes))
        return ';'.join(map(str,r))

class BDDExperiment(Experiment):
    def __init__(self, name, problem, method, collapse, compute_count, bound, op_req=None):
        super().__init__(name, problem)
        self.method = method
        self.collapse = collapse
        self.compute_count = compute_count
        self.bound = bound
        self.op_req = op_req

    def run(self, repeat):
        start = time.time()
        for i in range(repeat):
            sol = verify(self.problem, self.method, collapse=self.collapse, bound=self.bound, op_req=self.op_req)
            if self.compute_count and self.method == VerifyMethod.allSymbolic:
                print("Number of solutions: {}".format(sol.count()))
        end = time.time()

        t = end-start
        return t / repeat, sol

    def __str__(self):
        return super().__str__() + ";reduce={};{}".format(self.collapse, self.method)

class BDDOptExperiment(Experiment):
    def __init__(self, name, problem, collapse, get_sequence, op_req = None):
        super().__init__(name, problem)
        self.collapse = collapse
        self.get_sequence = get_sequence
        self.op_req = op_req

    def run(self, repeat):
        start = time.time()
        for i in range(repeat):
            sol = get_optimal(self.problem, self.get_sequence, collapse=self.collapse, op_req=self.op_req)
        end = time.time()
        t = end-start
        return t / repeat, sol
    
    def __str__(self):
        return super().__str__() + ";reduce={};opt".format(self.collapse)

class NetSynthExperiment(Experiment):
    def __init__(self, name, problem):
        super().__init__(str(name), problem)

    def run(self, folder, repeat):
        spec = NetSynthSpec(self.problem)
        t, seq  = spec.execute(folder + "/" + self.name + ".ltl", repeat)
        return t /repeat, seq

    def __str__(self):
        return super().__str__() + ";NS;rule" 

class FLIPExperiment(Experiment):
    def __init__(self, name, problem):
        super().__init__(str(name), problem)
    
    def run(self, repeat):
        spec = FLIPSpec(self.problem)
        t, seq = spec.execute(repeat)

        return t / repeat, seq

    def __str__(self):
        return super().__str__() + ";FLIP;nodup"


class PersimmonExperiment(Experiment):
    def __init__(self, name, problem):
        super().__init__(str(name), problem)

    def run(self, repeat):
        spec = PersimmonSpec(self.problem)
        t, seq = spec.execute(repeat)

        return t / repeat, seq

    def __str__(self):
        return super().__str__() + ";PERS;base"


class KakiExperiment(Experiment):
    def __init__(self, name, problem):
        super().__init__(str(name), problem)

    def run(self, repeat):
        spec = KakiSpec(self.problem)
        t, seq = spec.execute(repeat)

        return t / repeat, seq

    def __str__(self):
        return super().__str__() + ";kaki;base"

class ExperimentRunner():
    def __init__(self,dump=False):
        self.experiments = []
        self.dump = dump

    def add(self, experiment):
        self.experiments.append(experiment)

    def runAll(self, repeat, res_folder):
        if res_folder != None:
            os.makedirs(res_folder, exist_ok=True)
        
        for e in self.experiments:
            if res_folder != None:
                res_name = res_folder + "/"
            else:
                res_name = ""
            print("Running {}".format(e.name))
            print("Policy: {}".format(e.problem.prop))
            print("Initial path of nodes: {}".format(e.problem.init_nodes))
            print("Final path of nodes: {}".format(e.problem.final_nodes))
            if isinstance(e, NetSynthExperiment):
                if res_folder != None:
                    ns_path = res_folder + "/ns"
                else:
                    ns_path = os.getcwd() + "/ns"
                    print("No directory specified, dumping NS files in current directory")
                    print(ns_path)

                os.makedirs(ns_path, exist_ok=True)
                t, sol = e.run(ns_path, repeat)
                res_name += "{}_ns".format(e.name)
            elif isinstance(e, FLIPExperiment):
                t, sol = e.run(repeat)
                res_name += "{}_flip".format(e.name)
            elif isinstance(e, BDDExperiment):
                t, sol = e.run(repeat)
                res_name += "{}_bdd".format(e.name)
                if self.dump and res_folder != None:
                    sol.dump(res_name)
            elif isinstance(e, BDDOptExperiment):
                t, sol = e.run(repeat)
                res_name += "{}_bdd".format(e.name)
            elif isinstance(e, PersimmonExperiment):
                t, sol = e.run(repeat)
                res_name += "{}_pers".format(e.name)
            elif isinstance(e, KakiExperiment):
                t, sol = e.run(repeat)
                res_name += "{}_kaki".format(e.name)
            else:
                raise ValueError("Wrong type of experiment")

            if res_folder != None:
                with open(res_name, "w") as f:
                    f.write(str(e) + ";" + str(t) + ";" +  str(sol) + "\n")
                    
                with open(res_folder + "/legend", "w") as f:
                    f.write("name;prop;#initonly;#finalOnly;#noChange;#change;#tool;#method;#time;#ans\n")

            print("Time: {}".format(t))
            print("Solution: {}".format(sol))
  
def run_all_GML(foldername, config, top_name, G, p1, p2, dump=False, num_copies=0, op_req=None):
    exp_runner = ExperimentRunner(dump=dump)
    #draw_error = {"Easynet.gml","Iinet.gml","Gambia.gml","Uninet.gml", "AsnetAm.gml",
    #        "Compuserve.gml", "Garr200902.gml", "Fatman.gml", "Garr201104.gml",
    #        "Garr201103.gml", "Nordu2005.gml", "Garr201003.gml", "Garr201007.gml", 
    #        "Garr200912.gml", "Twaren.gml", "PionierL1.gml", }
    #not_draw = {dir_path + n for n in draw_error}
    exp_name = str(num_copies) + top_name
    for prop in config.props:
        if config.restrict:
            if config.bound == None:
                p = SynthesisProblem(p1,p2,prop(p1,p2),restricted=config.restrict)
            else:
                p1_path = get_shortest_path_edges(G, p1)
                p2_path = get_shortest_path_edges(G, p2)
                p = SynthesisProblem(p1_path,p2_path,prop(p1,p2),top=G,restricted=config.restrict)  

        elif not config_restrict:
            p1_path = get_shortest_path_edges(G, p1)
            p2_path = get_shortest_path_edges(G, p2)
            p = SynthesisProblem(p1_path,p2_path,prop(p1,p2),top=G,restricted=config.restrict)

            if config.bound == None:
                p.is_weighted=False

        if "NS" in config.tools:
            e_ns = NetSynthExperiment(exp_name,p)
            exp_runner.add(e_ns)
        if "BDD" in config.tools:
            for m in config.methods:
                for c in config.collapse:
                    e_bdd = BDDExperiment(exp_name,p,m,c,config.compute_count,config.bound, op_req=op_req)
                    exp_runner.add(e_bdd)
        if "FLIP" in config.tools:
            e_flip = FLIPExperiment(exp_name,p)
            exp_runner.add(e_flip)
        if "PERS" in config.tools:
            e_pers = PersimmonExperiment(exp_name, p)
            exp_runner.add(e_pers)
        if "kaki" in config.tools:
            e_kaki = KakiExperiment(exp_name, p)
            exp_runner.add(e_kaki)

    exp_runner.runAll(config.repeat, foldername)

def run_all_GML_opt(foldername, config, top_name, G, p1, p2, dump=False, num_copies=0, op_req=None):
    exp_runner = ExperimentRunner(dump=dump)

    p1_path = get_shortest_path_edges(G, p1)
    p2_path = get_shortest_path_edges(G, p2)

    exp_name = str(num_copies) + top_name

    for prop in config.props:
        prop_bdd = Conjunction(prop(p1,p2), LoopFreedom())
        p = SynthesisProblem(p1_path, p2_path, prop_bdd, top=G,restricted=config.restrict)
        for c in config.collapse:
            e = BDDOptExperiment(exp_name, p, c, config.get_sequence, op_op_req=op_reqreq)
            exp_runner.add(e)
    
    exp_runner.runAll(config.repeat, foldername)

def run_all(foldername, config, generator, r, dump=False, op_req=None):
    exp_runner = ExperimentRunner(dump=dump)
    for i in r:
        p1, p2 = generator(i)

        if config.bound != None:
            G, p1_path, p2_path = gen_topology(p1, p2, weighted=True)

        for prop in config.props:
            if config.bound != None:
                p = SynthesisProblem(p1_path, p2_path, prop(p1,p2), top=G, restricted=config.restrict)
            else:
                p = SynthesisProblem(p1,p2,prop(p1,p2),restricted=config.restrict)

            if "NS" in config.tools:
                e_ns = NetSynthExperiment(i,p)
                exp_runner.add(e_ns)
            if "BDD" in config.tools:
                for m in config.methods:
                    for c in config.collapse:
                        e_bdd = BDDExperiment(i,p,m,c,config.compute_count,config.bound,op_req=op_req)
                        exp_runner.add(e_bdd)
            if "FLIP" in config.tools:
                e_flip = FLIPExperiment(i,p)
                exp_runner.add(e_flip)
            if "PERS" in config.tools:
                e_pers = PersimmonExperiment(i, p)
                exp_runner.add(e_pers)
            if "kaki" in config.tools:
                e_kaki = KakiExperiment(i, p)
                exp_runner.add(e_kaki)

    exp_runner.runAll(config.repeat, foldername)

def run_all_opt(foldername, config, generator, r, dump=False, op_req=None):
    exp_runner = ExperimentRunner()

    for i in r:
        p1, p2 = generator(i)

        G, p1_path, p2_path = gen_topology(p1, p2, weighted=True)
        for prop in config.props:
            p = SynthesisProblem(p1_path, p2_path, prop(p1,p2), top=G, restricted=config.restrict)
            for c in config.collapse:
                e = BDDOptExperiment(str(i), p, c, config.get_sequence, op_req=op_req)
                exp_runner.add(e)

    exp_runner.runAll(config.repeat, foldername)   
