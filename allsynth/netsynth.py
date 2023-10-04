from subprocess import run, PIPE
import os

class NetSynthSpec:
    def __init__(self, problem):
        self.switches = []
        self.links = []
        self.prop = None
        self.generate(problem)

    def __str__(self):
        sw = sorted(self.switches, key=lambda s:s.id, reverse=True)

        temp = "{}\n{}\nspec\n{}"

        sw_str = '\n'.join(map(str, sw))
        l_str = '\n'.join(map(str, self.links))

        return temp.format(sw_str,l_str,self.prop)

    def execute(self, filename, repeat=1):
        with open(filename, "w") as f:
            f.write(str(self))

        time = 0
        ans = True

        print(os.path.dirname(__file__))
        print (os.path.relpath(__file__))
        
        for i in range(repeat):
            seq = []
            cmd = ["netsynth", "solve", filename, '-rule']
            proc = run(cmd, stdout=PIPE)
            res = proc.stdout.decode("utf-8")
            lines = res.splitlines()

            for l in range(len(lines)):
                print(lines[l])
                if "no correct update exists" in lines[l]:
                    seq = None
                    break
                if "finished synthesizing update" in lines[l]:
                    start = lines[l].find('(')
                    end = lines[l].find(')')
                    time += float(lines[l][start+1:end-1])
                    if ans == True and time > 0:
                        l = l + 2
                        while "num_wait" not in lines[l]:
                            print(lines[l])
                            pairs = lines[l].split("#")
                            for k in pairs:
                                start = k.find('(')
                                end = k.find(':')
                                update = int(k[start+1:end])
                                seq.append(update)
                            l = l + 1
                        break
                    else:
                        break

        return time / repeat, seq

    def generate(self, problem):
        self.prop = problem.prop.to_NetSynth()
        p1 = problem.init_nodes
        p2 = problem.final_nodes
 
        nodes = set(p1 + p2) # p2 shares src and dst with p1
        num_nodes = len(nodes)

        for n in nodes:
            p_in = "in{}s".format(n)
            p_out = "out{}s".format(n)

            # Generate switches and ports
            ports = [p_in, p_out]

            if n in p1 and n in p2:
                if n!= p1[-1]:
                    p_out_alt = p_out + "_2"
                    ports.append(p_out_alt)
            sw = Switch(n, ports)

            # If switch is only in p1, only initial rule

            if n in p1:
                sw.add_rule(p_in,p_out,True)
            if n in p2 and (n not in p1):
                sw.add_rule(p_in,p_out,False)
            if n in p2 and n in p1:
                if n != p1[-1]:
                    sw.add_rule(p_in,p_out_alt,False)
            if n == p1[-1]:
                sw.add_rule(p_in,p_out,False)

            self.switches.append(sw)

            # Add links between in/out ports
            links = []
            if n == p1[-1]:
                links.append(Link(p_out,p_out))
            else:
                if n in p1:
                    p_in_next = "in{}s".format(p1[p1.index(n)+1])
                    links.append(Link(p_out,p_in_next))
                if n in p2 and (n not in p1):
                    p_in_next = "in{}s".format(p2[p2.index(n)+1])
                    links.append(Link(p_out,p_in_next))
                if n in p1 and n in p2:
                    p_in_next = "in{}s".format(p2[p2.index(n)+1])
                    links.append(Link(p_out_alt,p_in_next))
                
                if n == p1[0]:
                    links.append(Link(None,p_in))
                
            for l in links:
                self.links.append(l)

class Switch:
    def __init__(self, id, ports):
        self.id = id
        self.ports = ports
        self.initial_rules = []
        self.final_rules = []

    def add_rule(self, port_in, port_out, initial=True):
        r = Rule(port_in, port_out)

        if initial:
            self.initial_rules.append(r)
        else:
            self.final_rules.append(r) 

    def __str__(self):
        temp = "switch {} ({}) [] {{ \n {} \n }} \n final {{ \n {} \n }}"

        i_rules = '\n'.join([str(r) for r in self.initial_rules])
        f_rules = '\n'.join([str(r) for r in self.final_rules])

        ports = ','.join(self.ports)

        return temp.format(self.id, ports, i_rules, f_rules)
        
class Rule:
    def __init__(self, port_in, port_out=None):
        self.port_in = port_in
        self.port_out = port_out

    def __str__(self):
        temp = "rule {} => {} []"
        if self.port_out == None:
            return temp.format(self.port_in,"")
        else:
            return temp.format(self.port_in,self.port_out)

class Link:
    def __init__(self, source, destination):
        self.src = source
        self.dst = destination

    def __str__(self):
        temp = "link {} => {} []"
        if self.src == None:
            return temp.format("",self.dst)
        else:
            return temp.format(self.src, self.dst)

class LTL:
    def __init__(self, prop):
        self.prop = prop
    
    def __str__(self):
        return self.prop.to_NetSynth()
