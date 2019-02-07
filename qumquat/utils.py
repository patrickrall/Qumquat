from .qvars import *

### Utility functions based on primitive operations
# Guideline: these should not require separate definitions for their inverses,
# but maybe they can inspect the superposition a bit for error checking
class Utils():
    def __init__(self, qq):
        self.qq = qq

    ######################### Casting

    def int(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(expr.c(b))
        newexpr.float = False
        return newexpr

    def float(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: float(expr.c(b))
        newexpr.float = True
        return newexpr

    ######################### Rounding

    def round(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(round(expr.c(b)))
        newexpr.float = False
        return newexpr

    def floor(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(math.floor(expr.c(b)))
        newexpr.float = False
        return newexpr

    def ceil(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(math.ceil(expr.c(b)))
        newexpr.float = False
        return newexpr


    ######################### Trig, sqrt

    def sin(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.sin(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def cos(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.cos(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def tan(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.tan(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def asin(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.asin(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def acos(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.acos(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def atan(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.atan(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def sqrt(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr, qq=self.qq)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.sqrt(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    ######################### QRAM

    def qram(self, dictionary, index):
        if not isinstance(index, Expression): index = Expression(index, qq=self.qq)
        if index.float:
            raise ValueError("QRAM keys must be integers, not floats.")

        # cast dictionaries to lists
        if isinstance(dictionary, list):
            dictionary = {i:dictionary[i] for i in range(len(dictionary))}

        casted_dict = {}

        isFloat = False

        for key in dictionary.keys():
            expr = Expression(dictionary[key], qq=self.qq)
            if expr.float: isFloat = True
            casted_dict[key] = expr

        newexpr = Expression(index)
        newexpr.c = lambda b: casted_dict[int(index.c(b))].c(b)
        newexpr.float = isFloat
        return newexpr

    ############ SWAP

    def swap(self, key1, key2):
        key1 -= key2 # a1 = a0-b0
        key2 += key1 # b1 = b0+a1 = a0
        key1 -= key2 # a2 = a1-b1 = -b0
        key1 *= -1

    ############ rotY
    # Just use state preparation for this (qq.init)?

    # apply a rotation around the Y axis, i.e. the matrix
    # [[ cos(theta), +sin(theta) ], [ sin(theta), cos(theta) ]]
    # when applied to |0> this yields cos(theta) |0> + sin(theta) |1>
    def rotY(self, x, i, theta):
        # Y_theta = S^dagger H Z_theta H S
        self.qq.phase_pi(x[i] / 2) # S
        x.had(i)
        self.qq.phase(-2*x[i]*theta) # Z_theta
        self.qq.phase(theta) # global phase correction
        x.had(i)
        self.qq.phase_pi(-x[i] / 2) # S^dagger


    ################### Snapshots

    def get_numpy(self):
        try:
            import numpy as np
        except ImportError:
            raise ImportError("Qumquat snapshots require numpy to be installed.")
        return np

    def snap(self, *regs):
        self.get_numpy()

        # check that registers are not expressions
        idxs = []
        for reg in regs:
            if not isinstance(reg, Key):
                raise SyntaxError("Can only take snapshot of quantum register, not expression.")
            idxs.append(reg.index())

        def branchesEqualNonIdxs(b1, b2):
            for key in self.qq.branches[b1].keys():
                if key == "amp": continue
                if key in idxs: continue
                if self.qq.branches[b1][key] != self.qq.branches[b2][key]: return False
            return True

        def branchesEqualIdxs(b1, b2):
            for idx in idxs:
                if self.qq.branches[b1][idx] != self.qq.branches[b2][idx]:
                    return False
            return True

        # sort branches into lists such that:
        # each list element has different values for idxs
        # each list element has the same value for non-idxs

        to_save = [[]]
        for branch in range(len(self.qq.branches)):
            i = 0
            while i < len(to_save):
                found = False

                if len(to_save[i]) > 0 and not branchesEqualNonIdxs(to_save[i][0], branch):
                    i += 1
                    continue

                for saved in to_save[i]:
                    if branchesEqualIdxs(saved, branch):
                        found = True
                        break

                if not found:
                    to_save[i].append(branch)
                    break

                i += 1

            if i == len(to_save):
                to_save.append([branch])

        # assemble density matrix
        rho = {}
        keys = []

        for i in range(len(to_save)):
            for j in range(len(to_save[i])):
                for k in range(len(to_save[i])):
                    key1, key2 = [], []
                    for idx in idxs: key1.append(str(self.qq.branches[to_save[i][j]][idx]))
                    for idx in idxs: key2.append(str(self.qq.branches[to_save[i][k]][idx]))
                    key1, key2 = " ".join(key1), " ".join(key2)

                    if key1 not in keys: keys.append(key1)
                    if key2 not in keys: keys.append(key2)

                    key = key1 + "x" + key2

                    val = self.qq.branches[to_save[i][j]]["amp"] * \
                            self.qq.branches[to_save[i][k]]["amp"].conjugate()

                    if key in rho: rho[key] += val
                    else: rho[key] = val

        return {
                "num_idxs": len(idxs),
                "keys": keys,
                "rho": rho,
            }

    def fidelity(self, snap1, snap2):
        np = self.get_numpy()

        if snap1["num_idxs"] != snap2["num_idxs"]:
            raise ValueError("Snapshots are on different number of registers.")

        keys = list(set(snap1["keys"]) | set(snap2["keys"]))
        rho1 = np.zeros((len(keys),len(keys))).astype(complex)
        rho2 = np.zeros((len(keys),len(keys))).astype(complex)

        for key in snap1["rho"].keys():
            key1, key2 = key.split("x")
            rho1[keys.index(key1)][keys.index(key2)] += snap1["rho"][key]

        for key in snap2["rho"].keys():
            key1, key2 = key.split("x")
            rho2[keys.index(key1)][keys.index(key2)] += snap2["rho"][key]

        eigvals, eigs = np.linalg.eigh(rho1)
        sqrtrho1 = np.dot(np.dot(eigs, np.diag([np.sqrt(x) for x in eigvals])), eigs.conj().T)
        eigvals = np.linalg.eigvalsh(np.dot(np.dot(sqrtrho1, rho2), sqrtrho1))
        return float(np.real(np.sqrt(eigvals).sum()))

    def trace_dist(self, snap1, snap2):
        np = self.get_numpy()

        if snap1["num_idxs"] != snap2["num_idxs"]:
            raise ValueError("Snapshots are on different number of registers.")

        keys = list(set(snap1["keys"]) | set(snap2["keys"]))
        diff = np.zeros((len(keys),len(keys))).astype(complex)

        for key in snap1["rho"].keys():
            key1, key2 = key.split("x")
            diff[keys.index(key1)][keys.index(key2)] += snap1["rho"][key]

        for key in snap2["rho"].keys():
            key1, key2 = key.split("x")
            diff[keys.index(key1)][keys.index(key2)] -= snap2["rho"][key]

        eigs = np.linalg.eigvalsh(diff)
        return float(np.real(sum([abs(x) for x in eigs])/2))
