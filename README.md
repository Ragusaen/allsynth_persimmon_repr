# AllSynth

A Python3 tool for complete and automatic synthesis of correct update sequences.

Abstract:
>The increasingly stringent dependability requirements on communication networks as well as the need to
>render these networks more adaptive to improve performance, demand for more automated approaches
>to operate networks. We present AllSynth, a novel symbolic synthesis tool for updating communication networks
>in a provably correct and efficient manner. To this end, AllSynth automatically synthesizes network update
>schedules which transiently ensure a wide range of policy properties (expressed in the LTL logic), also
>during the reconfiguration process. In particular, in contrast to existing approaches, AllSynth symbolically 
>computes and compactly represents all feasible solutions.
>At its heart, AllSynth relies on a novel, two-level and parameterized use of BDDs which greatly
>improves performance. Indeed, AllSynth not only provides formal correctness guarantees and outperforms
>existing state-of-the-art tools in terms of generality, but also in terms of runtime as documented by experiments on a large benchmark of >real-world network topologies.


## Getting Started

AllSynth relies heavily on the dd package from https://github.com/tulip-control/dd for manipulating (reduced ordered) binary decision diagrams (BDDs).

How to install:

```
pip3 download dd --no-deps
tar xzf dd-*.tar.gz
cd dd-*/
python3 setup.py install --fetch --cudd
```

Other dependencies can be installed also with pip3:

```
pip3 install matplotlib
pip3 install pandas
```

### Netsynth
The tool NetSynth (https://dl.acm.org/doi/10.1145/2737924.2737980) is included as a binary.

Make NetSynth globally executable (e.g placing it in /usr/local/bin).

NetSynth relies on the Yices library, version 1.0.39.
Please refer to (https://yices.csl.sri.com/) for how to obtain Yices.

### FLIP
The tool FLIP (https://ieeexplore.ieee.org/document/7524419) can be found here: https://gitlab.com/s.vissicchio/flip-vm.

Make sure that FLIP can be found e.g by adding the main directory to your PYTHONPATH.

FLIP relies on Python2 and its dependencies can be installed as follows, with pip2 already installed:

```
pip2 install pulp
python2 -m pip install -i https://pypi.gurobi.com gurobipy
python2 -m pip install networkx==1.11
```

Note that the default gurobi license may not be sufficient for the largest models.

Please refer to https://www.gurobi.com/academia/academic-program-and-licenses/ for how to obtain an academic license.

## Usage
AllSynth has a number of parameter which can be set from the command-line.

To see the full list of options, run:

```
python3 run.py -h
```

## A small example

We will in this example consider update synthesis for a small instance of the diamond class of models.

Concretely, we consider a topology consisting only of two paths, where the nodes on the paths are given as follows:

initial = 0, 1, 2, 3, 4

final  = 0, 6, 7, 8, 4

and where the policy is `Reach(4)`

Running AllSynth with the following command, all solutions are synthesizes as one ROBDD:

```
python3 run.py -t BDD -e diamond --index 5 --e-prop Reach 
```

As a part of the output, we get the time it takes to synthesize the set of all correct uppdate sequences, as well as an indication of whether this set is empty:

```
Policy: (Reach 4)
Initial path of nodes: [0, 1, 2, 3, 4]
Final path of nodes: [0, 6, 7, 8, 4]
Time: 0.006152629852294922
Solution: non-empty
```

To get a concrete update sequence, we add the `--some` argument:

```
python3 run.py -t BDD -e diamond --index 5 --e-prop Reach  --some
```

The tools now also outputs

```
Solution: (set(), [8, 6, 7, 0], {1, 2, 3, 4})
```

The first empty set indicates that no switches were updated before the actual synthesis procedure executed.

The middle list provides a correct sequence of switch updates. First node 8 must be updated to forward traffic to 4, then 6 to 7, 7 to 8, essentially establishing path 6-7-8, before updating 0 to route traffic to 6.

The final set includes all trivial nodes that do not change routing or is only present on the initial path.


To fully use Lemma 2.9 reduction, we add the `--reduce` argument:

```
python3 run.py -t BDD -e diamond --index 5 --e-prop Reach  --some --reduce
```

and get the following output:

```
Solution: ({8, 6, 7}, [0], {1, 2, 3, 4})
```

The first set includes all switches that may be updated (in any order) before synthesizing a correct update sequence for the remaining nodes (now only node 0).

To count the number of solution, the --count argument can be provided instead of `--some`:

```
python3 run.py -t BDD -e diamond --index 5 --e-prop Reach  --reduce --count
python3 run.py -t BDD -e diamond --index 5 --e-prop Reach  --count
```

If the reduction is used, the tool counts 1 solution and otherwise 6 as one may update 6,7,8 in any order as long as 0 is updated at the end.

## Rerunning experiments
To rerun the experiments presented in the paper, we have provided a number of scripts in the scripts/ directory.
(must be run from the root directory)

All experiments use a timeout of 2 hours and a memory limit of 14GB.


To rerun the full diamond experiments:

```
./scripts/run_all.sh scripts/run_dia.sh dia_res 100 1000 50 "Reach SC SeparateWPk" 
```

To rerun the full topology zoo experiments:

```
./scripts/run_all_topzoo.sh topzoo_res "Reach SC SeparateWPk" 5 topologies/topzoo
```

After a succesfull run, one may gather the results as follows:

```
python3 gather_results.py dia_res
python3 gather_results.py topzoo_res 50
```

This will create X.csv files for each prop X in dia_res and topzoo_res.

To then create the plots presented in the paper, execute the following:
```
python3 allsynth/merge_plots topzoo_res/Reach-time.mkplot topzoo_res/SC-time.mkplot topzoo_res/Reach-SC
python3 mkplot/mkplot.py -c mkplot/zoo_reach_sc.json --save-to fig10a topzoo_res/Reach-SC.mkplot
python3 mkplot/mkplot.py -c mkplot/zoo_wp.json --save-to fig10b topzoo_res/SeparateWPk-time.mkplot

python3 mkplot/mkplot.py -c mkplot/dia.json --save-to fig10c dia_res/Reach-time.mkplot
python3 mkplot/mkplot.py -c mkplot/dia.json --save-to fig10d dia_res/SeparateWPk-time.mkplot
```

The plots are now created in the root folder as fig10a, fig10b, fig10c and fig10d.










