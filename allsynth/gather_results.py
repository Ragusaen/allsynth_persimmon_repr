import sys
import os
import pandas as pd
import glob
from dd.cudd import load
from bddbase import BDDbase

ULIMIT = 1000*1000*14
TIMELIMIT = 3600*2
ERR = -1
TIMEOUT = -3

class CorrectnessError(Exception):
    """BDD allsym does not agree with NS/FLIP answer."""

class FoldersMissingError(Exception):
    """ Expected folders missing. """

def read_log(filename):
    res = 0
    with open(filename,'r') as f:
        for line in f:
            if "verify.IdenticalPathsError" in line:
                res = ERR

            if "DisconnectedError" in line:
                res = ERR

            if "oom-kill" in line:
                res =  ERR
            
            if "DUE TO TIME LIMIT" in line:
                res = ERR

            if "Maximum resident set size (kbytes):" in line and res != ERR:
                res = int(line.split(":")[1])
                if res >= ULIMIT:
                    res = ERR
                else:
                    res = res / 1000
    return res


def gather_results_prefix(folder , prefix):
    print("Gathering results for {}".format(prefix))

    # Get data. If legend does not exist, no data
    legend = folder + "/{}-0/legend".format(prefix)
    try:
        header = pd.read_csv(legend, sep=";", names=None).columns
    except FileNotFoundError:
        return pd.DataFrame()

    all_files = glob.glob(folder + "/{}-*/*_{}".format(prefix, prefix.lower()))
    res = pd.concat((pd.read_csv(f, sep=";", names=list(header)) for f in all_files))

    # Get memory from .log file
    log_files = [f.replace("_" + prefix.lower(), ".log") for f in all_files]
    
    mem = dict()

    for f in log_files:
        # Must be int for sorting
        name = f.split("/")[-1].split(".")[0]
        if "gml" not in f:
            name = int(name)
            
        peak_mem = read_log(f)

        if name in mem:
            mem[name].append(peak_mem)
        else:
            mem[name] = [peak_mem]

    mem = dict(sorted(mem.items()))

    mem_ls = []

    for name in mem:
        mem_ls += mem[name]

    res.sort_values(by=['name'],inplace=True)


    res["mem MB"] = mem_ls
    return res

def compute_averages(res):
    for kind in res:
        if not res[kind].empty:
            h = list(res[kind])
            h.remove("#time")
            h.remove("mem MB")
            h.remove("#ans")
            res[kind] = res[kind].groupby(h).agg({'#time': 'mean', 'mem MB': 'mean', '#ans': 'any'}).reset_index()
            res[kind].loc[res[kind]["mem MB"] == ERR, '#time'] = ERR



def load_bdd_dddmp(filename):
    base = BDDbase()

    print("Trying to load {}".format(filename))
    sols = []
    u = load(filename + "_bdd", base.bdd,reordering=True)[0]

    z_nodes = sorted([int(z.strip('z')) for z in base.bdd.support(u) if z.startswith('zz')])

    base.Z = ['z' + str(z) for z in z_nodes]
    base.ZZ = ['z' + str(z) for z in base.Z]
    assert len(base.Z) + len(base.ZZ) == len(base.bdd.support(u))

    # There is one BDD for each Z
    for z in range(len(base.Z)+1):
        fname = filename + "_bdd_{}.dddmp".format(z)
        sols.append(base.bdd.load(fname)[0])
    
    return base, sols

def compare_results(other, allsym, bdd_folder):
    #print("Comparing {} with {} in {}".format(other, allsym, bdd_folder))
    shared = set(other['name']).intersection(set(allsym['name']))

    for s in shared:
        seq = list(other[other['name'] == s]['#ans'])[0].strip("[]").split(",")
        seq = [int(n) for n in seq]

        base, sols = load_bdd_dddmp(bdd_folder + "/{}".format(s))

        seq = [n for n in seq if ('z' + str(n)) in base.Z]

        if len(seq) == 0:
            if sols[-1] == base.bdd.false:
                correct = True
            else:
                correct = False
        else:
            print(seq)
            correct = base.is_solution(seq, sol=sols)

        if not correct:
            raise CorrectnessError("BDD correctness fail on {}/{}_bdd".format(bdd_folder,s))
        else:
            print("{} validated!".format(s))

def gather_results_prop(prop_folder, check=False):
    (_, subdirs, _) = next(os.walk(prop_folder))
    print("gathering {} results".format(prop_folder))
    res = {}

    if "allsym" in subdirs:
        res["allsym"]  = gather_results_prefix(prop_folder + "/allsym", "BDD")

    #if "opt" in subdirs:
    #    res["opt"]  = gather_results_prefix(prop_folder + "/opt", "BDD")

    if "reduce" in subdirs:
        res["reduce"]  = gather_results_prefix(prop_folder + "/reduce", "BDD")

    #if "reduce_opt" in subdirs:
    #    res["reduce_opt"]  = gather_results_prefix(prop_folder + "/reduce_opt", "BDD")

    if "NS" in subdirs:
        res["NS"]  = gather_results_prefix(prop_folder + "/NS", "NS")

    if "FLIP" in subdirs:
        res["FLIP"] = gather_results_prefix(prop_folder + "/FLIP", "FLIP")

    if "PERS" in subdirs:
        res["PERS"] = gather_results_prefix(prop_folder + "/PERS", "PERS")

    if "kaki" in subdirs:
        res["kaki"] = gather_results_prefix(prop_folder + "/kaki", "kaki")
        res["kaki"].loc[:, '#ans'] = 'unknown'

    compute_averages(res)

    concat = pd.concat(list(res.values()))

    if check:
        ns_df = concat[(concat['#tool'] == "NS") & (concat['mem MB'] != -1)]

        allsym_df = concat[(concat['#tool'] == "reduce=False") & (concat['#method'] == "VerifyMethod.allSymbolic")]

        print("Comparing allsym to NS")
        compare_results(ns_df, allsym_df, prop_folder + "/allsym/BDD-0")

        if "SC" not in prop_folder:
            print("Comparing allsym to FLIP")
            flip_df = concat[(concat['#tool'] == "FLIP") & (concat['mem MB'] != ULIMIT)]
            compare_results(flip_df, allsym_df, prop_folder + "/allsym/BDD-0")

    return concat

def gather_results_all(folder, check=False):
    (_, subdirs, _) = next(os.walk(folder))

    res = dict()
    for sd in subdirs:
        res[sd] = gather_results_prop(folder + "/{}".format(sd), check)
    return res

def save_results(res, save_folder, pick_num):
    os.makedirs(save_folder, exist_ok=True)
    plots = dict()
    for r in res:
        print(r)
        res[r].to_csv(save_folder + "/{}.csv".format(r), sep=";", index=False)
        print("Gathering time")
        plots[r] = to_mkplot(res[r], "#time",pick_num)
        
        plots[r].to_csv(save_folder + "/{}-time.mkplot".format(r),sep=" ", index=False)
        #print("Gathering mem")
        #to_mkplot(res[r], "mem MB", pick_num).to_csv(save_folder + "/{}-mem.mkplot".format(r),sep=" ", index=False)

    #concat_plot = mkplot_concatenate(plots)
    #concat_plot.to_csv(save_folder + "/allprop-time.mkplot",sep=" ", index=False)

def mkplot_concatenate(plots):
    print("Concatenating")
    new_table = pd.DataFrame()

    props = ["Reach", "SeparateWPk", "SC"]
    for prop in props:
        if prop not in plots:
            continue
        p = plots[prop]

        if prop == "SeparateWPk":
            prop = "WP"
        p.rename(columns={ c : "{} {}".format(c, prop).replace(" ","-") for c in p.columns if c != "instance"}, inplace=True)

        for c in p.columns:
            if c != "instance":
                new_table[c] = p[c]

    new_table.insert(loc=0, column='instance', value=["instance" + str(i) for i in range(len(new_table.index)) ])
    new_table.fillna(ERR,inplace=True)
    print(new_table)
    return new_table

def to_mkplot(res, col, pick_num=None):
    tools = res["#tool"].unique()

    to_csv = pd.DataFrame()

    tmp_data = []

    for t in tools:
        data = res[(res["#tool"] == t)]       
        methods = data["#method"].unique()
        header = t   

        if "False" in t:
            continue
        elif "True" in t:
            header = "AllSynth"

        for m in methods:
            time = data[(data["#method"] == m)]
            time = time[col]   

            if "opt" in m:
                header = header+"-"+m

            if pick_num != None:
                pick_num = int(pick_num)
                cp = time.copy()
                cp.sort_values(inplace=True, ascending=False)

                num_DNF = len(cp[cp ==  -1])

                if num_DNF > 0:
                    DNF_series = pd.Series([-1 for i in range(min(pick_num, num_DNF))])
                    cp = cp.head(int(max(0, pick_num-num_DNF)))

                    cp = pd.concat([DNF_series.reset_index(drop=True), cp.reset_index(drop=True)])
                else:
                    cp = cp.head(pick_num)

                to_csv[header] = cp.reset_index(drop=True)

            else:
                to_csv[header] = time.copy()


    instances = ["instance" + str(i) for i in range(len(to_csv.index))]
    to_csv.insert(loc=0, column='instance', value=instances)
    if col == "#time":
        to_csv.fillna(ERR,inplace=True)
        #to_csv.replace(ERR, "", inplace=True)
    elif col == "mem MB":
        to_csv.fillna(ERR, inplace=True)
        #to_csv.replace(ERR, "", inplace=True)
    return to_csv

if __name__ == '__main__':
    folder = sys.argv[1]
    save_folder = sys.argv[1]

    if len(sys.argv) > 2:
        pick_num = sys.argv[2]
    else:
        pick_num = None
    
    #verify = sys.argv[2]

    #if verify == "1":
    #    verify = True
    #else:
    #    verify = False    
        
    res = gather_results_all(folder, False)

    save_results(res, save_folder, pick_num)



