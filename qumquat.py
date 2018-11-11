from qvars import *
from random import random
import math, copy, cmath


class Qumquat(object):

    branches = [{"amp": 1+0j}]

    queue_stack = [] # list of list of action tuples

    def queue_action(self, action, *data):
        if len(self.queue_stack) == 0: return False
        self.queue_stack[-1].append((action,data))
        return True

    def call(self, tup, invert=False):
        if not invert:
            getattr(self, tup[0])(*tup[1])
        else:
            if tup[0][-4:] == "_inv":
                getattr(self, tup[0][:-4])(*tup[1])
            else:
                getattr(self, tup[0]+"_inv")(*tup[1])

    controls = [] # list of expressions

    # any keys affecting controls cannot be modified
    def assert_mutable(self, key):
        if not isinstance(key, Key):
            raise SyntaxError("Operation can only be performed on registers, not expressions.")
        for ctrl in self.controls:
            if key.key in ctrl.keys:
                raise SyntaxError("Cannot modify value of controlling register.")

    # only operate on branches where controls are true
    def controlled_branches(self):
        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        return [b for b in self.branches if goodbranch(b)]

    key_count = 0
    reg_count = 0
    key_dict = {} # dictionary of registers for each key

    pile_stack = []  # lookup table for indices
    garbage_piles = {"keyless": []}  # storage for keyed garbage piles
    garbage_stack = []


    ############################ Alloc and dealloc

    def alloc(self, key):
        if self.queue_action('alloc', key): return
        self.assert_mutable(key)

        # print("alloc", key)

        reg = self.reg_count
        self.key_dict[key.key].append(reg)
        self.reg_count += 1

        for branch in self.branches: branch[reg] = es_int(0)

    def alloc_inv(self, key):
        if self.queue_action('alloc_inv', key): return
        self.assert_mutable(key)

        # print("dealloc", key)

        if key.allocated():
            target = key
            proxy = None
        else:
            target = key.partner()
            proxy = key

        # remove the register from the branches and key_dict
        for branch in self.branches: branch.pop(target.index())
        self.key_dict[target.key].remove(target.index())

        # if target is out of registers, remove both from pile
        if len(self.pile_stack) > 0 and not target.allocated():
            if proxy is not None:
                # remove proxy
                for i in range(len(self.pile_stack[-1])):
                    if self.pile_stack[-1][i].key == proxy.key:
                        del self.pile_stack[-1][i]
                        break

            # remove target
            for i in range(len(self.pile_stack[-1])):
                if self.pile_stack[-1][i].key == target.key:
                    del self.pile_stack[-1][i]
                    break



    ########################### User functions for making and deleting registers

    def reg(self, *vals):
        out = []
        for val in vals:

            key = Key(self)
            out.append(key)

            # print("newkey", key)

            if len(self.garbage_stack) > 0:
                gkey = self.garbage_stack[-1]

                if gkey == "keyless":
                    self.garbage_piles["keyless"][-1].append(key)
                else:
                    self.garbage_piles[gkey].append(key)

            self.alloc(key)
            self.init(key, val)

        if len(out) > 1: return tuple(out)
        else: return out[0]

    def clean(self, key, val):
        self.init_inv(key, val)
        self.alloc_inv(key)


    ############################ Initialization

    # takes a register in the |0> state and initializes it to the desired value
    def init(self, key, val):
        if self.queue_action('init', key, val): return
        self.assert_mutable(key)

        for branch in self.branches:
            if branch[key.index()] != 0: raise ValueError("Register already initialized!")

        # cast ranges to superpositions, permitting qq.reg(range(3))
        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)

        if isinstance(val, list):
            # uniform superposition
            for i in range(len(val)):
                if not (isinstance(val[i], int) or isinstance(val[i], es_int)):
                    raise TypeError("Superpositions only support integer literals.")
                if val.index(val[i]) != i:
                    raise ValueError("Superpositions can't contain repeated values.")

            newbranches = []
            for branch in self.branches:
                for x in val:
                    newbranch = copy.copy(branch)
                    newbranch[key.index()] = es_int(x)
                    newbranch["amp"] /= math.sqrt(len(val))
                    newbranches.append(newbranch)

            self.branches = newbranches

        elif isinstance(val, int) or isinstance(val, es_int):
            for branch in self.branches:
                branch[key.index()] = es_int(val)

        elif isinstance(val, Expression):
            if val.float: raise TypeError("Quantum registers can only contain ints")
            for branch in self.branches:
                branch[key.index()] = es_int(val.c(branch))
        else:
            raise TypeError("Quantum registers can only contain ints")

    # takes a register and a guess for what state it is in
    # if the guess is correct, the register is set to |0>
    def init_inv(self, key, val):
        if self.queue_action('init_inv', key, val): return
        self.assert_mutable(key)


        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)

        if isinstance(val, list):
            for i in range(len(val)):
                if not (isinstance(val[i], int) or isinstance(val[i], es_int)):
                    raise TypeError("Superpositions only support non-superposed integers.")
                if val.index(val[i]) != i:
                    raise TypeError("Superpositions can't contain repeated values.")

            # populate newbranches with branches matching first list item
            newbranches = []
            for branch in self.branches:
                if branch[key.index()] != val[0]: continue

                b = copy.copy(branch)
                b[key.index()] = 0
                newbranches.append(b)

            if len(self.branches) != len(newbranches)*len(val):
                raise ValueError("Failed to clean superposition.")

            # check if other list items match up
            for i in range(1,len(val)):
                found = [] # list of indices in newbranches, where partners were found in branches
                for branch in self.branches:
                    if branch[key.index()] != val[i]: continue

                    matched = False
                    for j in range(len(newbranches)):
                        if j in found: continue

                        good = True
                        for k in newbranches[j].keys():
                            if k == key.index(): continue
                            if newbranches[j][k] != branch[k]:
                                good = False
                                break

                        if good:
                            found.append(j)
                            matched = True
                            break

                    if not matched:
                        raise ValueError("Failed to clean superposition.")
                if len(found) < len(newbranches):
                    raise ValueError("Failed to clean superposition.")

            self.branches = newbranches
            for branch in self.branches:
                branch["amp"] *= math.sqrt(len(val))

        elif isinstance(val, int) or isinstance(val, es_int):
            for branch in self.branches:
                if branch[key.index()] != val:
                    raise ValueError("Failed to uncompute: not all branches matched specified value.\n (Expected "+str(val)+" but found branch with "+str(branch[key.index()])+". Register: "+str(key.index())+", key:"+str(key.key)+")")
                branch[key.index()] = 0
        elif isinstance(val, Expression):
            if key.key in val.keys:
                raise SyntaxError("Can't clean register using its own value.")

            for branch in self.branches:
                if branch[key.index()] != val.c(branch):
                    raise ValueError("Failed to clean: not all branches matched specified value.")
                branch[key.index()] = 0
        else:
            raise TypeError("Quantum registers can only contain ints")

    ######################################## Measurement and printing

    def distribution(self, *exprs):
        def cast(ex):
            if isinstance(ex, str):
                class Dummy():
                    def c(s, b): return ex
                return Dummy()
            return Expression(ex, self)

        def dofloat(ex):
            if isinstance(ex, str):
                return ex
            else: return round(float(ex), 10)

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

        return values, probs, configs

    def measure(self, *var):
        if len(self.mode_stack) > 0:
            raise SyntaxError("Can only measure at top-level.")

        values, probs, configs = self.distribution(*var)

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

    def print(self, *exprs):
        if self.queue_action('print', *exprs): return

        values, probs, configs = self.distribution(*exprs)
        s = []

        # print distribution
        for i in range(len(values)):
            if isinstance(values[i], tuple):
                st = " ".join([str(x) for x in list(values[i])])
            else: st = str(values[i])
            s.append(st + " w.p. " + str(round(probs[i],5)))
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
            else: return round(float(ex), 10)

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
            r = round(r,5)
            if phi == 0:
                return str(r)

            rounded = round(phi/cmath.pi,10)
            if round(rounded,5) == rounded:
                if int(rounded) == 1:
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

    ######################################## Primitive operations

    # Todo: O(n) implementation possible?
    def had(self, key, bit):
        if self.queue_action('had', key, bit): return
        self.assert_mutable(key)
        bit = Expression(bit, self)
        if key.key in bit.keys: raise SyntaxError("Can't hadamard variable in bit depending on itself.")

        def branchesEqual(b1, b2):
            for key in b1.keys():
                if key == "amp": continue
                if b1[key] != b2[key]: return False
            return True

        newbranches = []
        def insert(oldbranch, trans, mult):
            oldbranch = copy.copy(oldbranch)
            oldbranch[key.index()] = trans(oldbranch[key.index()])

            for branch in newbranches:
                if branchesEqual(branch, oldbranch):
                    branch["amp"] += oldbranch["amp"]*mult/math.sqrt(2)
                    return

            newbranches.append(oldbranch)
            newbranches[-1]["amp"] *= mult/math.sqrt(2)


        for branch in self.controlled_branches():
            idx = bit.c(branch)

            if idx == -1: # -1 is sign bit
                insert(branch, lambda x: x, 1)
                insert(branch, lambda x: -x, -branch[key.index()].sign)
            else:
                if abs(int(branch[key.index()])) & (1 << idx) == 0:
                    insert(branch, lambda x: x, 1)
                    insert(branch, lambda x: es_int(x.sign)*(abs(x) + 2**idx), 1)
                else:
                    insert(branch, lambda x: es_int(x.sign)*(abs(x) - 2**idx), 1)
                    insert(branch, lambda x: x, -1)

        self.branches = []

        norm = 0
        for branch in newbranches:
            if abs(branch["amp"]) > 1e-10:
                self.branches.append(branch)
                norm += abs(branch["amp"])**2

        for branch in self.branches:
            branch["amp"] /= math.sqrt(norm)

    def had_inv(self, key, bit):
        self.had(key, bit)

    # for things like +=, *=, etc
    def oper(self, key, expr, do, undo):
        if self.queue_action('oper', key, expr, do, undo): return
        self.assert_mutable(key)
        if key.key in expr.keys:
            raise SyntaxError("Can't modify target based on expression that depends on target.")

        for branch in self.controlled_branches():
            branch[key.index()] = do(branch)

    def oper_inv(self, key, expr, do, undo):
        self.oper(key, expr, undo, do)

    def phase(self, theta):
        if self.queue_action('phase', theta): return
        theta = Expression(theta, self)

        for branch in self.controlled_branches():
            branch['amp'] *= cmath.exp(1j*theta.c(branch))

    def phase_inv(self, theta):
        self.phase(-theta)

    def phase_pi(self, theta): self.phase(theta*math.pi)
    def phase_2pi(self, theta): self.phase(2*theta*math.pi)

    def cnot(self, key, idx1, idx2):
        if self.queue_action('cnot', key, idx1, idx2): return
        self.assert_mutable(key)

        idx1 = Expression(idx1, self)
        idx2 = Expression(idx2, self)

        if key.key in idx1.keys or key.key in idx2.keys:
            raise SyntaxError("Can't modify target based on expression that depends on target.")

        for branch in self.controlled_branches():
            v_idx1 = idx1.c(branch)
            v_idx2 = idx2.c(branch)
            if v_idx1 == v_idx2: raise ValueError("Can't perform CNOT from index to itself.")
            if branch[key.index()][v_idx1] == 1:
                branch[key.index()][v_idx2] = 1 - branch[key.index()][v_idx2]

    def cnot_inv(self, key, idx1, idx2):
        self.cnot(key, idx1, idx2)


    ################################################ Code regions

    mode_stack = []
    def push_mode(self, mode):
        self.mode_stack.append(mode)

    def pop_mode(self, mode):
        if len(self.mode_stack) == 0:
            raise SyntaxError("Mismatched delimeter "+mode+": no starting delimeter")
        x = self.mode_stack[-1]
        if x != mode:
            raise SyntaxError("Mismatched delimeter "+mode+": expected end "+x)
        self.mode_stack.pop()


   ######################## Invert

    def inv(self):
        class WrapInv():
            def __enter__(s):
                self.push_mode("inv")
                self.queue_stack.append([])

            def __exit__(s, *args):
                self.pop_mode("inv")

                queue = self.queue_stack.pop()
                for tup in queue[::-1]:
                    self.call(tup, invert=True)

        return WrapInv()

    ################### If

    def q_if(self, expr):
        expr = Expression(expr, self)
        class WrapIf():
            def __enter__(s):
                self.do_if(expr)

            def __exit__(s, *args):
                self.do_if_inv(expr)

        return WrapIf()

    def do_if(self, expr):
        if self.queue_action("do_if", expr): return
        self.controls.append(expr)

    def do_if_inv(self, expr):
        if self.queue_action("do_if_inv", expr): return
        self.controls.pop()

    ################### While

    def q_while(self, expr, key):
        expr = Expression(expr, self)
        class WrapWhile():
            def __enter__(s):
                self.queue_stack.append([])

            def __exit__(s, *args):
                queue = self.queue_stack.pop()
                self.do_while(queue, expr, key)

        return WrapWhile()

    def do_while(self, queue, expr, key):
        if self.queue_action("do_while", queue, expr, key): return
        self.assert_mutable(key)

        for branch in self.controlled_branches():
            if branch[key.index()] != 0: raise ValueError("While loop variable must be initialized to 0.")
        if key.key in expr.keys: raise SyntaxError("While loop expression cannot depend on loop variable.")

        count = 0
        while True:
            # check if all branches are done
            if all([expr.c(b) == 0 for b in self.controlled_branches()]): break

            with self.q_if(expr): key += 1

            with self.q_if(key > count):
                for tup in queue: self.call(tup)

            count += 1


    def do_while_inv(self, queue, expr, key):
        if self.queue_action("do_while_inv", queue, expr, key): return
        self.assert_mutable(key)

        if key.key in expr.keys: raise SyntaxError("While loop expression cannot depend on loop variable.")

        # initial count is maximum value of key
        count = max([b[key.index()] for b in self.controlled_branches()])

        # loop only depends on value of key
        while True:
            if count == 0: break

            count -= 1

            with self.q_if(key > count):
                for tup in queue[::-1]: self.call(tup, invert=True)

            with self.q_if(expr): key -= 1


    ################### Garbage

    # https://python-3-patterns-idioms-test.readthedocs.io/en/latest/PythonDecorators.html
    # What a mess: a class that can be both a with wrapper and a decorator,
    # and the decorator supports arguments AND no arguments

    def garbage(self, *keys):
        if len(keys) == 0:
            key = "keyless"
        else:
            key = keys[0]
            if key == "keyless":
                raise SyntaxError("'keyless' is a reserved garbage pile key.")

        class WrapGarbage():
            def enter(s):
                self.garbage_stack.append(key)
                if key == "keyless":
                    self.garbage_piles["keyless"].append([])
                else:

                    if key not in self.garbage_piles:
                        self.garbage_piles[key] = []

                self.queue_stack.append([])

            def exit(s):
                queue = self.queue_stack.pop()

                if key == "keyless":
                    pile = self.garbage_piles["keyless"].pop()
                else:
                    pile = self.garbage_piles[key]

                self.garbage_stack.pop()
                self.do_garbage(queue, pile, key)

            def __call__(s, f):
                def wrapped(*args):
                    s.enter()
                    out = f(*args)
                    s.exit()
                    return out

                return wrapped

            def __enter__(s): s.enter()

            def __exit__(s, *args): s.exit()


        return WrapGarbage()


    def do_garbage(self, queue, pile, key):
        if self.queue_action("do_garbage", queue, pile, key): return

        self.pile_stack.append(pile)

        for tup in queue: self.call(tup)

        if key=="keyless" and len(pile) > 0:
            raise SyntaxError("Keyless garbage pile terminated non-empty.")

        self.pile_stack.pop()


    def do_garbage_inv(self, queue, pile, key):
        if self.queue_action("do_garbage_inv", queue, pile, key): return

        self.queue_stack.append([]) # just reverse the queue
        for tup in queue[::-1]: self.call(tup, invert=True)
        rev_queue = self.queue_stack.pop()

        self.do_garbage(rev_queue, pile, key)

    def assert_pile_clean(self, key):
        if self.queue_action("assert_pile_clean", key): return
        if key not in self.garbage_piles: return
        if len(self.garbage_piles[key]) == 0: return
        raise ValueError("Garbage pile '"+key+"' is not clean.")

    def assert_pile_clean_inv(self, key):
        if self.queue_action("assert_pile_clean_inv", key): return
        self.assert_pile_clean(key)


import sys
sys.modules[__name__] = Qumquat()


