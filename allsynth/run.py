from io import open_code
from experiments import *
from functools import partial
from verify import VerifyMethod
from experiments import VerifyConfig, OptimizeConfig
from property_parsing import parse_property
from property import Conjunction
import sys
import argparse
import os
import textwrap

if __name__ == '__main__':
    progname = "AllSynth"
    formatter = argparse.RawTextHelpFormatter
    parser = argparse.ArgumentParser(prog = progname, formatter_class=formatter)
    parser.description = """Running update synthesis tool"""

    group = parser.add_argument_group("Tool and experiment options")
    group.add_argument("-t", dest="tool", required=True, help="Tool {BDD, NS, FLIP, PERS}")

    exclusive_group = group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument("-e", dest="exper", help="Run experiment on predefined scalable topology {zigzag, zigzag_inverse, confluent, diamond}")
    exclusive_group.add_argument("--GML", metavar=("f","j"), nargs=2, dest="gml", help="Run GML file f experiment, concatenated j times")

    # Experiment settings group
    group = parser.add_argument_group("Experiment configuration")
    group.add_argument("--index", type=int, metavar="i", help="Index of experiment to run for non-topzoo experiments")
    exclusive_group = group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument("--e-prop",  dest="prop", metavar="p", help="Predefined experiment property {Reach, WP, SC, SeparateWPk, Unsat}.")
    exclusive_group.add_argument("--prop",  dest="prop_file",  metavar="f", help="Primary LTL policy (defaults to parse f as property string).")
    group.add_argument("--op-req", metavar="f", dest="op_req", required=False, help="Secondary operator LTL policy")

    group.add_argument("--repeat", nargs="?", metavar="r", default=1, type=int, help="Number of times to repeat experiment (default r=1)")


    # Specific BDD settings
    group = parser.add_argument_group("BDD synthesis options")
    group.add_argument("--reduce", default=False, action="store_true", help="Use reduction for BDD synthesis")
    group.add_argument("--opt", default=False, action="store_true", help="Get optimal value")
    group.add_argument("-u", default=False, action="store_true", help="Synthesize general solutions")
    group.add_argument("--some", default=False, action="store_true", help="Synthesize some solution")
    group.add_argument("--count", default=False, action="store_true", help=textwrap.dedent('''\
                                                                            Get number of solutions.
                                                                            If -u specified, counts solutions of length equal to
                                                                            the number of edges in topology
                                                                            '''))
    group.add_argument("--weight-bound", metavar="b", type=int, help="Constrains solutions to respect b")

    # Dump settings
    group = parser.add_argument_group("Dump options")
    group.add_argument("--dir", metavar="f", dest="savedir", help ="Where to save results (created if not exists)")
    group.add_argument("--dump-bdd", dest="dump_bdd", default=False, action="store_true", help="Dump BDDs as .dddmp")

    # Retrieve values
    args = parser.parse_args()
    tool = args.tool
    exper = args.exper
    index = args.index
    repeat = args.repeat
    collapse = args.reduce
    savedir = args.savedir
    dump_bdd = args.dump_bdd
    optimal = args.opt
    unrestricted = args.u
    get_sequence = args.some
    gml = args.gml
    get_count = args.count
    weight_bound= args.weight_bound

    print(args)

    # Property initialization
    k = 5

    # Add reachability if BDD or NS as FLIP automatically detects loops and blackholes
    if args.prop:
        prop = args.prop
        if prop == "Reach":
            inv = Property.get_reachability
        elif prop == "WP":
            inv = partial(Property.get_waypoint_every, k)
            if tool == "BDD" or tool == "NS" or tool == "PERS" or tool == "kaki":
                inv = partial(Property.get_conjunction, inv, Property.get_reachability)
        elif prop == "SC":
            inv = partial(Property.get_servicechain, k)
            if tool == "BDD" or tool == "NS" or tool == "PERS" or tool == "kaki":
                inv = partial(Property.get_conjunction, inv, Property.get_reachability)
        elif prop == "Unsat":
            inv = Property.get_waypoint_only_initial_midway
        elif prop == "SeparateWP":
            inv = Property.get_sep_waypoint
            if tool == "BDD" or tool == "NS" or tool == "PERS" or tool == "kaki":
                inv = partial(Property.get_conjunction, inv, Property.get_reachability)
        elif prop == "SeparateWPk":
            inv = partial(Property.get_sep_waypoint_every, k)
            if tool == "BDD" or tool == "NS" or tool == "PERS" or tool == "kaki":
                inv = partial(Property.get_conjunction, inv, Property.get_reachability)
        else:
            print("Unknown property")
            exit(0)

    elif args.prop_file:
        try:
            prop = parse_property(args.prop_file)
            # Wrap in lambda...
            inv = lambda p1,p2: prop
        except Exception as e:
            print(e)
            exit(0)

    if args.op_req:
        op_req_ltl = parse_property(args.op_req)
    else:
        op_req_ltl = None

    if unrestricted and (weight_bound or optimal):
        raise NotImplementedError("Support for general solutions for quantitative problems not yet implemented")

    #if unrestricted and get_count:
    #    raise NotImplementedError("Support for counting generals solutions not yet implemented")

    # method
    if get_sequence:
        if get_count:
            raise NotImplementedError("Support for --some and --count not yet implemented")
        method = VerifyMethod.some
    else:
        method = VerifyMethod.allSymbolic

    if get_count and optimal:
        raise NotImplementedError("--count is not supported for --opt (so far)")

    if dump_bdd and savedir == None:
        raise NotImplementedError("Must supply --dir with --dump-bdd")

    if optimal:
        config = OptimizeConfig([inv], [collapse], repeat=repeat, restrict= not unrestricted, get_sequence = get_sequence)
    else:
        config = VerifyConfig([inv], [method], [collapse], [tool], repeat=repeat, restrict= not unrestricted, compute_count = get_count, bound=weight_bound)

    if exper:
        # Experiments mapping
        gen_map = {"zigzag" : gen_zigzag,
                    "zigzag_inverse" : partial(gen_zigzag, inverse=True),
                    "confluent": gen_confluent,
                    "diamond": gen_diamondSeparateWP }

        # Experiment configuration
        if optimal:
            gen = gen_map[exper]
            run_all_opt(savedir, config, gen, range(index, index+1), dump=dump_bdd, op_req=op_req_ltl)

        else:
            gen = gen_map[exper]
            run_all(savedir, config, gen, range(index, index+1), dump=dump_bdd, op_req=op_req_ltl)

    elif gml != None:
        gml_path = args.gml[0]
        num_copies = int(args.gml[1])

        (G, p1, p2) = gen_init_final(gml_path, num_copies=num_copies)

        suffix = gml_path.split('/')[-1]
        if optimal:
            run_all_GML_opt(savedir, config, suffix, G, p1, p2, dump=dump_bdd, num_copies=num_copies, op_req=op_req_ltl)
        else:
            run_all_GML(savedir, config, suffix, G, p1, p2, dump=dump_bdd, num_copies=num_copies, op_req=op_req_ltl)

