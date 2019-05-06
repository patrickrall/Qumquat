from .qvars import *
import math, copy

class Init:

    ############################ Initialization

    # takes a register in the |0> state and initializes it to the desired value
    def init(self, key, val):
        if self.queue_action('init', key, val): return
        self.assert_mutable(key)

        for branch in self.controlled_branches():
            if branch[key.index()] != 0: raise ValueError("Register already initialized!")

        # cast ranges to superpositions, permitting qq.reg(range(3))
        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)
        if isinstance(val, int) or isinstance(val, es_int): val = Expression(val, self)

        if isinstance(val, Expression):
            if val.float: raise TypeError("Quantum registers can only contain ints")
            for branch in self.controlled_branches():
                branch[key.index()] = es_int(val.c(branch))

        elif isinstance(val, list):
            # uniform superposition over elements in list

            # check list for validity
            for i in range(len(val)):
                if not (isinstance(val[i], int) or isinstance(val[i], es_int)):
                    raise TypeError("Superpositions only support integer literals.")
                if val.index(val[i]) != i:
                    raise ValueError("Superpositions can't contain repeated values.")

            newbranches = []
            goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
            for branch in self.branches:
                if goodbranch(branch):
                    for x in val:
                        newbranch = copy.copy(branch)
                        newbranch[key.index()] = es_int(x)
                        newbranch["amp"] /= math.sqrt(len(val))
                        newbranches.append(newbranch)
                else:
                    newbranches.append(branch)

            self.branches = newbranches
        elif isinstance(val, dict):
            # check if dictionary has integer keys, cast values to expressions
            for k in val.keys():
                if not isinstance(k, int): raise TypeError("QRAM keys must be integers.")
                val[k] = Expression(val[k], qq=self)

            newbranches = []
            goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
            for branch in self.branches:
                if goodbranch(branch):

                    norm = 0
                    for k in val.keys(): norm += abs(float(val[k].c(branch)))**2
                    if abs(norm) < self.thresh: raise ValueError("State from dictionary has norm 0.")

                    for k in val.keys():
                        newbranch = copy.copy(branch)
                        newbranch[key.index()] = es_int(k)
                        newbranch["amp"] *= float(val[k].c(branch))/math.sqrt(norm)
                        if (abs(newbranch["amp"]) != 0):
                            newbranches.append(newbranch)
                else:
                    newbranches.append(branch)

            self.branches = newbranches
        else:
            raise TypeError("Invalid initialization of register with type ", type(val))

    # takes a register and a guess for what state it is in
    # if the guess is correct, the register is set to |0>
    def init_inv(self, key, val):
        if self.queue_action('init_inv', key, val): return
        self.assert_mutable(key)

        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)
        if isinstance(val, int) or isinstance(val, es_int): val = Expression(val, self)

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        if isinstance(val, Expression):
            for branch in self.branches:
                if goodbranch(branch): target = val.c(branch)
                else: target = 0

                if branch[key.index()] != target:
                    raise ValueError("Failed to uncompute: not all branches matched specified value.\n\
                            (Expected "+str(target)+" but found branch with "+str(branch[key.index()])+")")
                    branch[key.index()] = es_int(0)

        elif isinstance(val, list):
            # uniform superposition

            # check valid
            for i in range(len(val)):
                if not (isinstance(val[i], int) or isinstance(val[i], es_int)):
                    raise TypeError("Superpositions only support non-superposed integers.")
                if val.index(val[i]) != i:
                    raise TypeError("Superpositions can't contain repeated values.")


            # populate newbranches with branches matching first list item
            untouchedbranches = []
            newbranches = []
            for branch in self.branches:
                if goodbranch(branch):
                    if branch[key.index()] != val[0]: continue

                    b = copy.copy(branch)
                    b[key.index()] = 0
                    newbranches.append(b)
                else:
                    untouchedbranches.append(branch)

            if len(self.branches) != len(newbranches)*len(val) + len(untouchedbranches):
                raise ValueError("Failed to clean superposition.")

            # check if other list items match up
            for i in range(1,len(val)):
                found = [] # list of indices in newbranches, where partners were found in branches
                for branch in self.branches:
                    if not goodbranch(branch): continue
                    if branch[key.index()] != val[i]: continue

                    matched = False
                    for j in range(len(newbranches)):
                        if j in found: continue

                        good = True
                        for k in newbranches[j].keys():
                            if k == key.index(): continue
                            if k == "amp":
                                if abs(newbranches[j][k] - branch[k]) > 1e-10:
                                    good = False
                                    break
                            elif newbranches[j][k] != branch[k]:
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
            self.branches += untouchedbranches

        elif isinstance(val, dict):
            # check if dictionary has integer keys, and get norm
            for k in val.keys():
                if not isinstance(k, int): raise TypeError("QRAM keys must be integers.")
                val[k] = Expression(val[k], qq=self)

            keys = list(val.keys())

            # check if branches are equal except for key.index()
            def branchesEqual(b1, b2):
                for idx in self.branches[b1].keys():
                    if idx == "amp": continue
                    if idx == key.index(): continue
                    if self.branches[b1][idx] != self.branches[b2][idx]:
                        return False
                return True

            untouchedbranches = []
            newbranches = []

            checkbranches = [] # list of branch indexes unique up to key.index()
            checkamplitudes = [] # factored amplitudes

            for b in range(len(self.branches)):
                branch = self.branches[b]
                if goodbranch(branch):
                    # if separable then branch should have this amplitude
                    amp = branch["amp"]
                    dict_amp = complex(val[int(branch[key.index()])].c(branch))
                    if dict_amp == 0:
                        raise ValueError("Failed to clean QRAM.")
                    amp /= dict_amp
                    norm = 0
                    for k in val.keys(): norm += abs(float(val[k].c(branch)))**2
                    if abs(norm) < self.thresh: raise ValueError("State from dictionary has norm 0.")
                    amp *= math.sqrt(norm)

                    found = False
                    i = 0
                    while i < len(checkbranches):
                        if branchesEqual(b, checkbranches[i]):
                            if abs(checkamplitudes[i] - amp) > 1e-10:
                                raise ValueError("Failed to clean QRAM.")
                            found = True
                            break
                        i += 1

                    if not found:
                        checkbranches.append(b)
                        checkamplitudes.append(amp)

                        newb = copy.copy(branch)
                        newb[key.index()] = es_int(0)
                        newb["amp"] = amp
                        newbranches.append(newb)
                else:
                    untouchedbranches.append(branch)


            self.branches = newbranches
            self.branches += untouchedbranches
        else:
            raise TypeError("Invalid un-initialization of register with type ", type(val))


