from .qvars import *
import cmath, copy

# primitive.py
#  - had, cnot, qft
#  - oper
#  - phase

# low priority TODO: can these be simplified using new prune function?

class Primitive:
    ######################################## Hadamard

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
        def insert(branch):

            for existingbranch in newbranches:
                if branchesEqual(branch, existingbranch):
                    existingbranch["amp"] += branch["amp"]
                    return
            newbranches.append(branch)

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        for branch in self.branches:
            if not goodbranch(branch):
                insert(branch)
            else:
                idx = bit.c(branch)
                newbranch1 = copy.deepcopy(branch)
                newbranch1["amp"] /= math.sqrt(2)
                newbranch1[key.index()] = es_int(branch[key.index()])
                newbranch1[key.index()][idx] = 0

                newbranch2 = copy.deepcopy(branch)
                newbranch2["amp"] /= math.sqrt(2)
                newbranch2[key.index()] = es_int(branch[key.index()])
                newbranch2[key.index()][idx] = 1

                if branch[key.index()][idx] == 1:
                    newbranch2["amp"] *= -1

                insert(newbranch1)
                insert(newbranch2)

        self.branches = newbranches
        self.prune()


    def had_inv(self, key, bit):
        self.had(key, bit)


    ######################################## QFT

    def qft(self, key, d, inverse=False):
        if self.queue_action('qft', key, d, inverse): return
        self.assert_mutable(key)
        d = Expression(d, self)
        if key.key in d.keys:
            raise SyntaxError("Can't modify target based on expression that depends on target.")

        def branchesEqual(b1, b2):
            for key in b1.keys():
                if key == "amp": continue
                if b1[key] != b2[key]: return False
            return True

        newbranches = []
        def insert(branch):
            for existingbranch in newbranches:
                if branchesEqual(branch, existingbranch):
                    existingbranch["amp"] += branch["amp"]
                    return
            newbranches.append(branch)

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        for branch in self.branches:
            if not goodbranch(branch):
                insert(branch)
            else:
                dval = d.c(branch)
                if dval != int(dval) or int(dval) <= 1:
                    raise ValueError("QFT must be over a positive integer")
                base = branch[key.index()] - (branch[key.index()] % dval)
                for i in range(int(dval)):
                    newbranch = copy.deepcopy(branch)
                    newbranch['amp'] *= 1/math.sqrt(dval)

                    if inverse:
                        newbranch['amp'] *= cmath.exp(-int(branch[key.index()])*i\
                                *2j*math.pi/int(dval))
                    else:
                        newbranch['amp'] *= cmath.exp(int(branch[key.index()])*i\
                                *2j*math.pi/int(dval))

                    newbranch[key.index()] = es_int(i + base)
                    newbranch[key.index()].sign = branch[key.index()].sign
                    insert(newbranch)


        self.branches = newbranches
        self.prune()

    def qft_inv(self, key, d, inverse=False):
        self.qft(key, d, inverse=(not inverse))


    ######################################## Primitives

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
            branch['amp'] *= cmath.exp(1j*float(theta.c(branch)))

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



