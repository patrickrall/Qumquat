from .qvars import *

# snapshot.py
#  - get_numpy
#  - snap
#  - fidelity
#  - trace_dist


class Snapshots:

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
            for key in self.branches[b1].keys():
                if key == "amp": continue
                if key in idxs: continue
                if self.branches[b1][key] != self.branches[b2][key]: return False
            return True

        def branchesEqualIdxs(b1, b2):
            for idx in idxs:
                if self.branches[b1][idx] != self.branches[b2][idx]:
                    return False
            return True

        # sort branches into lists such that:
        # each list element has different values for idxs
        # each list element has the same value for non-idxs

        to_save = [[]]
        for branch in range(len(self.branches)):
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
                    for idx in idxs: key1.append(str(self.branches[to_save[i][j]][idx]))
                    for idx in idxs: key2.append(str(self.branches[to_save[i][k]][idx]))
                    key1, key2 = " ".join(key1), " ".join(key2)

                    if key1 not in keys: keys.append(key1)
                    if key2 not in keys: keys.append(key2)

                    key = key1 + "x" + key2

                    val = self.branches[to_save[i][j]]["amp"] * \
                            self.branches[to_save[i][k]]["amp"].conjugate()

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
