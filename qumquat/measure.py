from .qvars import *
import cmath, math
from random import random

# measure.py
#  - dist
#  - measure
#  - postselect
#  - print, print_amp

class Measure:
    ######################################## Measurement and printing

    def dist(self, *exprs, branches=False):
        def cast(ex):
            if isinstance(ex, str):
                class Dummy():
                    def c(s, b): return ex
                return Dummy()
            return Expression(ex, self)

        def dofloat(ex):
            if isinstance(ex, str):
                return ex
            else: return round(float(ex), self.print_expr_digs)

        exprs = [cast(expr) for expr in exprs]

        values = []
        configs = []
        probs = []

        for i in range(len(self.branches)):
            branch = self.branches[i]

            if len(exprs) == 1:
                val = dofloat(exprs[0].c(branch))
            else:
                val = tuple([dofloat(expr.c(branch)) for expr in exprs])

            if val not in values:
                values.append(val)
                configs.append([i])
                probs.append(abs(branch["amp"])**2)
            else:
                idx = values.index(val)
                configs[idx].append(i)
                probs[idx] += abs(branch["amp"])**2

        idxs = list(range(len(probs)))
        idxs.sort(key=lambda i:values[i])

        values = [values[i] for i in idxs]
        probs = [probs[i] for i in idxs]
        configs = [configs[i] for i in idxs]

        if branches:
            return values, probs, configs
        else:
            return values, probs

    def measure(self, *var):
        if len(self.mode_stack) > 0:
            raise SyntaxError("Can only measure at top-level.")

        # still need to queue since measuring is allowed inside garbage collected environment
        if self.queue_action('measure', *var): return

        values, probs, configs = self.dist(*var, branches=True)

        # pick outcome
        r = random()
        cumul = 0
        pick = -1
        for i in range(len(probs)):
            if cumul + probs[i] > r:
                pick = i
                break
            else: cumul += probs[i]

        # collapse superposition
        self.branches = [self.branches[i] for i in configs[pick]]
        for branch in self.branches:
            branch["amp"] /= math.sqrt(probs[pick])

        return values[pick]

    def postselect(self, expr):
        if len(self.mode_stack) > 0:
            raise SyntaxError("Can only measure at top-level.")

        if self.queue_action('postselect', expr): return

        expr = Expression(expr, self)

        newbranches = []
        prob = 0
        for branch in self.branches:
            if expr.c(branch) != 0:
                newbranches.append(branch)
                prob += abs(branch["amp"])**2

        if len(newbranches) == 0:
            raise ValueError("Postselection failed!")
        self.branches = newbranches

        for branch in self.branches:
            branch["amp"] /= math.sqrt(prob)

        return float(prob)

    def print(self, *exprs):
        if self.queue_action('print', *exprs): return

        values, probs, configs = self.dist(*exprs, branches=True)
        s = []

        # print distribution
        for i in range(len(values)):
            if isinstance(values[i], tuple):
                st = " ".join([str(x) for x in list(values[i])])
            else: st = str(values[i])
            s.append(st + " w.p. " + str(round(probs[i],self.print_prob_digs)))
        print("\n".join(s))

    def print_inv(self, *exprs):
        if self.queue_action('print_inv', *exprs): return
        self.print(*exprs)

    def print_amp(self, *exprs):
        if self.queue_action('print_amp', *exprs): return

        def cast(ex):
            if isinstance(ex, str):
                class Dummy():
                    def c(s, b): return ex
                return Dummy()
            return Expression(ex, self)
        exprs = [cast(expr) for expr in exprs]

        values = []
        amplitudes = {}

        def dofloat(ex):
            if isinstance(ex, str):
                return ex
            else: return round(float(ex), self.print_expr_digs)

        for i in range(len(self.branches)):
            branch = self.branches[i]

            if len(exprs) == 1:
                val = dofloat(exprs[0].c(branch))
            else:
                val = tuple([dofloat(expr.c(branch)) for expr in exprs])

            if val not in values:
                amplitudes[len(values)] = [branch["amp"]]
                values.append(val)
            else:
                idx = values.index(val)
                amplitudes[idx].append(branch["amp"])
        s = []
        idxs = list(range(len(values)))
        idxs.sort(key=lambda i:values[i])

        def show_amp(a):
            r,phi = cmath.polar(a)
            r = round(r,self.print_prob_digs)
            if phi == 0:
                return str(r)

            rounded = round(phi/cmath.pi,self.print_prob_digs*2)
            if round(rounded,self.print_prob_digs) == rounded:
                if int(rounded) in [-1, 1]:
                    return "-"+str(r)
                elif rounded == 0.5:
                    return "1j*"+str(r)
                elif rounded == -0.5:
                   return "-1j*"+str(r)
                elif rounded == 0:
                    return str(r)
                else:
                    return str(r)+"*e^("+str(rounded)+"*pi*i)"

            return str(r)+"*e^(i*"+str(phi)+")"

        # print distribution
        for i in idxs:
            amps = ", ".join([show_amp(a) for a in amplitudes[i]])
            if isinstance(values[i], tuple):
                st = " ".join([str(x) for x in list(values[i])])
            else: st = str(values[i])

            s.append(st + " w.a. " + amps)
        print("\n".join(s))

    def print_amp_inv(self, *exprs):
        if self.queue_action('print_amp_inv', *exprs): return
        self.print_amp(*exprs)


