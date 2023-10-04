from subprocess import run, PIPE
import os

import importlib
FLIP_HELPER_PATH = os.path.dirname(__file__) + "/flip_helper.py"

class FLIPSpec:
    def __init__(self, problem):
        if importlib.util.find_spec("flip") == None:
            raise ImportError("FLIP not installed")
        else:
            self.FLIP_DIR = importlib.util.find_spec("flip").origin.replace("flip.py", "")
        self.init = problem.init_nodes
        self.final = problem.final_nodes
        self.subpaths = problem.prop.to_FLIP(self.init, self.final)

    def execute(self, repeat):
        time = 0

        init_arg = ["-init", ' '.join(map(str, self.init))]
        final_arg = ["-final", ' '.join(map(str, self.final))]

        sub_paths = []
        for s in self.subpaths:
            sub_paths += ["-subpaths", ' '.join(map(str, s))]

        print("Flip subpaths: {}".format(sub_paths))
        time = 0
        for i in range(repeat):
            seq = []
            cmd = ["python2", "-W", "ignore", FLIP_HELPER_PATH] + init_arg + final_arg + sub_paths
            proc = run(cmd, stdout=PIPE, cwd=self.FLIP_DIR)
            res = proc.stdout.decode("utf-8")

            if proc.stderr != None:
                res_error = proc.stderr.decode("utf-8")
                print(res_error)
            lines = res.splitlines()

            for l in range(len(lines)):
                print(lines[l])
                if "OP<" in lines[l] and "migrate" in lines[l]:
                    start = lines[l].find("<")
                    end = lines[l].find(">")
                    seq.append(int(lines[l][start+1:end]))
                if "TIME=" in lines[l]:
                    start = lines[l].find("=")
                    time += float(lines[l][start+1:])
        return time,  seq