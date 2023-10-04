import re
import tempfile
from ast import literal_eval
from subprocess import run, PIPE


class KakiSpec:
    def __init__(self, problem):
        self.init = problem.init_nodes
        self.final = problem.final_nodes
        self.properties = problem.prop.to_kaki()

    def execute(self, repeat):
        initial_routing = list(map(lambda x: list(x), zip(self.init[:-1], self.init[1:])))
        final_routing = list(map(lambda x: list(x), zip(self.final[:-1], self.final[1:])))

        problem = '{"Initial_routing":' + str(initial_routing) + ',"Final_routing":' + str(final_routing) + ',"Properties":{"Waypoint": { "startNode": -1, "finalNode": -1, "waypoint": []}, "LoopFreedom": { "startNode": -1},' + self.properties + '}}'
        problem = problem.replace('"startNode":-1', f'"startNode":{self.init[0]}')

        print(problem)

        problem_file = tempfile.NamedTemporaryFile()
        problem_file.write(str.encode(problem))
        problem_file.flush()

        time = 0
        for _ in range(repeat):
            cmd = ["java", "-jar", "kaki/translate.jar", "kaki/verifypn-linux64", problem_file.name]
            proc = run(cmd, stdout=PIPE, stderr=PIPE)
            res = proc.stdout.decode("utf-8")

            print('Kaki stdout: ', res)
            print('Kaki stderr: ', proc.stderr.decode('utf-8'))
            time += float(re.search(r"Total program runtime: (\d+\.?\d*) seconds", res)[1])
        return time, []