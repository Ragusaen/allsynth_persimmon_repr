import re
from ast import literal_eval
from subprocess import run, PIPE


class PersimmonSpec:
    def __init__(self, problem):
        self.init = problem.init_nodes
        self.final = problem.final_nodes
        self.properties = problem.prop.to_persimmon()

    def execute(self, repeat):
        initial_routing = list(map(lambda x: list(x), zip(self.init[:-1], self.init[1:])))
        final_routing = list(map(lambda x: list(x), zip(self.final[:-1], self.final[1:])))

        problem = '{"Initial_routing":' + str(initial_routing) + ',"Final_routing":' + str(final_routing) + ',"Properties":{' + self.properties + '}}'
        problem = problem.replace('"startNode":-1', f'"startNode":{self.init[0]}')

        time = 0
        for _ in range(repeat):
            print('Persimmon problem: ', problem)
            cmd = ["./persimmon", "-c", problem]
            proc = run(cmd, stdout=PIPE, stderr=PIPE)
            res = proc.stdout.decode("utf-8")

            print('Persimmon stdout: ', res)
            print('Persimmon stderr: ', proc.stderr.decode('utf-8'))
            time += float(re.search(r"Time elapsed\(s\): (\d+\.?\d*)s", res)[1])
            m = re.search(r'Solution: (?:Some\(([^)]*)\)|None)', res)[1]
            seq = literal_eval(m)
        return time,  seq
