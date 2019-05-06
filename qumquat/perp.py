from .qvars import *
import copy

class Perp:
    # sets orth to 1 if key is perpendicular to val, 0 otherwise
    def perp_init(self, key, orth, val):
        if self.queue_action('perp_init', key, orth, val): return
        self.assert_mutable(orth)

        for branch in self.controlled_branches():
            if branch[orth.index()] != 0: raise ValueError("Register already initialized!")

        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)
        if isinstance(val, int) or isinstance(val, es_int): val = Expression(val, self)

        def branchesEqual(b1, b2):
            for key in b1.keys():
                if key == "amp": continue
                if b1[key] != b2[key]: return False
            return True

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        if isinstance(val, Expression):
            if val.float: raise TypeError("Can only reflect around integers")
            for branch in self.controlled_branches():
                branch[orth.index()] = es_int(branch[key.index()] != val.c(branch))

        elif isinstance(val, list):
            # check list for validity
            for i in range(len(val)):
                if not (isinstance(val[i], int) or isinstance(val[i], es_int)):
                    raise TypeError("Superpositions only support integer literals.")
                if val.index(val[i]) != i:
                    raise ValueError("Superpositions can't contain repeated values.")
            N = len(val)

            # can superpositions support expressions? Not at the moment....

            newbranches = []
            for branch in self.branches:
                if not goodbranch(branch):
                    newbranches.append(branch)
                    continue

                # if key is not in the list always flip
                found = False
                for i in range(N):
                    if branch[key.index()] == val[i]:
                        found = True
                        break

                if not found:
                    branch[orth.index()] = es_int(1)
                    newbranches.append(branch)
                    continue

                # key is in superposition: need to create 2*N branches
                for j in range(N):
                    amp0 = 0j
                    amp1 = 0j

                    for i in range(N):
                        if branch[key.index()] == val[i]:
                            amp0 += branch["amp"]/N
                            amp1 += branch["amp"]*((1 if i==j else 0)-1/N)

                    br0 = copy.deepcopy(branch)
                    br0["amp"] = amp0
                    br0[key.index()] = val[j]

                    br1 = copy.deepcopy(branch)
                    br1["amp"] = amp1
                    br1[key.index()] = val[j]
                    br1[orth.index()] = es_int(1)

                    def insertBranch(br):
                        found = False
                        for newbranch in newbranches:
                            if branchesEqual(br,newbranch):
                                newbranch["amp"] += br["amp"]
                                found = True
                                break
                        if not found:
                            newbranches.append(br)
                    insertBranch(br0)
                    insertBranch(br1)

            self.branches = newbranches
            self.prune()

        elif isinstance(val, dict):
            # check if dictionary has integer keys, cast values to expressions
            for k in val.keys():
                if not isinstance(k, int): raise TypeError("QRAM keys must be integers.")
                val[k] = Expression(val[k], qq=self)
                if key.key in val[k].keys or orth.key in val[k].keys:
                    raise SyntaxError("Can't measure target with state that depends on target.")

            newbranches = []
            for branch in self.branches:
                if not goodbranch(branch):
                    newbranches.append(branch)
                    continue

                norm = 0j
                for k in val.keys():
                    norm += abs(complex(val[k].c(branch)))**2
                if abs(norm) < self.thresh: raise ValueError("State from dictionary has norm 0.")

                # if key is not in the list always flip
                found = False
                for k in val.keys():
                    if branch[key.index()] == k:
                        found = True
                        break

                if not found:
                    branch[orth.index()] = es_int(1)
                    newbranches.append(branch)
                    continue

                for k1 in val.keys():
                    amp0 = 0j
                    amp1 = 0j

                    for k2 in val.keys():
                        if branch[key.index()] == k2:
                            proj = complex(val[k2].c(branch))*complex(val[k1].c(branch)).conjugate()/norm
                            amp0 += branch["amp"]*proj
                            amp1 += branch["amp"]*((1 if k1==k2 else 0)-proj)

                    br0 = copy.deepcopy(branch)
                    br0["amp"] = amp0
                    br0[key.index()] = k1

                    br1 = copy.deepcopy(branch)
                    br1["amp"] = amp1
                    br1[key.index()] = k1
                    br1[orth.index()] = es_int(1)

                    def insertBranch(br):
                        found = False
                        for newbranch in newbranches:
                            if branchesEqual(br,newbranch):
                                newbranch["amp"] += br["amp"]
                                found = True
                                break
                        if not found:
                            newbranches.append(br)
                    insertBranch(br0)
                    insertBranch(br1)

            self.branches = newbranches
            self.prune()
        else:
            raise TypeError("Invalid initialization of perpendicular register with type ", type(val))


    def perp_init_inv(self, key, orth, val):
        if self.queue_action('perp_init_inv', key, orth, val): return
        self.assert_mutable(key)

        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)
        if isinstance(val, int) or isinstance(val, es_int): val = Expression(val, self)

        def branchesEqual(b1, b2):
            for key in b1.keys():
                if key == "amp": continue
                if b1[key] != b2[key]: return False
            return True

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        if isinstance(val, Expression):
            if val.float: raise TypeError("Can only reflect around integers")
            for branch in self.branches:
                if goodbranch(branch): target = es_int(branch[key.index()] != val.c(branch))
                else: target = 0

                if branch[orth.index()] != target:
                    raise ValueError("Failed to uncompute perpendicular bit.")

                branch[key.index()] = es_int(0)

        elif isinstance(val, list):
            # check list for validity
            for i in range(len(val)):
                if not (isinstance(val[i], int) or isinstance(val[i], es_int)):
                    raise TypeError("Superpositions only support integer literals.")
                if val.index(val[i]) != i:
                    raise ValueError("Superpositions can't contain repeated values.")
            N = len(val)

            newbranches = []
            for branch in self.branches:
                if not goodbranch(branch):
                    if branch[orth.index()] != 0:
                        raise ValueError("Failed to uncompute perpendicular bit.")

                    newbranches.append(branch)
                    continue

                # if key is not in the list always flip
                found = False
                for i in range(N):
                    if branch[key.index()] == val[i]:
                        found = True
                        break

                if not found:
                    if branch[orth.index()] != 1:
                        raise ValueError("Failed to uncompute perpendicular bit.")

                    branch[orth.index()] = es_int(0)
                    newbranches.append(branch)
                    continue

                # key is in superposition: need to create 2*N branches
                for j in range(N):
                    amp0 = 0j
                    amp1 = 0j

                    for i in range(N):
                        if branch[key.index()] == val[i]:
                            amp0 += branch["amp"]/N
                            amp1 += branch["amp"]*((1 if i==j else 0)-1/N)

                    br0 = copy.deepcopy(branch)
                    br0["amp"] = amp0
                    br0[key.index()] = val[j]

                    br1 = copy.deepcopy(branch)
                    br1["amp"] = amp1
                    br1[key.index()] = val[j]
                    br1[orth.index()] = 1-br1[orth.index()]

                    def insertBranch(br):
                        found = False
                        for newbranch in newbranches:
                            if branchesEqual(br,newbranch):
                                newbranch["amp"] += br["amp"]
                                found = True
                                break
                        if not found:
                            newbranches.append(br)
                    insertBranch(br0)
                    insertBranch(br1)

            self.branches = newbranches
            self.prune()

            for branch in self.branches:
                if branch[orth.index()] != 0:
                    raise ValueError("Failed to uncompute perpendicular bit.")

        elif isinstance(val, dict):
            # check if dictionary has integer keys, cast values to expressions
            for k in val.keys():
                if not isinstance(k, int): raise TypeError("QRAM keys must be integers.")
                val[k] = Expression(val[k], qq=self)
                if key.key in val[k].keys or orth.key in val[k].keys:
                    raise SyntaxError("Can't measure target with state that depends on target.")

            newbranches = []
            for branch in self.branches:
                if not goodbranch(branch):
                    if branch[orth.index()] != 0:
                        raise ValueError("Failed to uncompute perpendicular bit.")

                    newbranches.append(branch)
                    continue

                norm = 0j
                for k in val.keys():
                    norm += abs(complex(val[k].c(branch)))**2
                if abs(norm) < self.thresh: raise ValueError("State from dictionary has norm 0.")

                # if key is not in the list always flip
                found = False
                for k in val.keys():
                    if branch[key.index()] == k:
                        found = True
                        break

                if not found:
                    if branch[orth.index()] != 1:
                        raise ValueError("Failed to uncompute perpendicular bit.")

                    branch[orth.index()] = es_int(0)
                    newbranches.append(branch)
                    continue

                for k1 in val.keys():
                    amp0 = 0j
                    amp1 = 0j

                    for k2 in val.keys():
                        if branch[key.index()] == k2:
                            proj = complex(val[k2].c(branch))*complex(val[k1].c(branch)).conjugate()/norm
                            amp0 += branch["amp"]*proj
                            amp1 += branch["amp"]*((1 if k1==k2 else 0)-proj)

                    br0 = copy.deepcopy(branch)
                    br0["amp"] = amp0
                    br0[key.index()] = k1

                    br1 = copy.deepcopy(branch)
                    br1["amp"] = amp1
                    br1[key.index()] = k1
                    br1[orth.index()] = 1-br1[orth.index()]

                    def insertBranch(br):
                        found = False
                        for newbranch in newbranches:
                            if branchesEqual(br,newbranch):
                                newbranch["amp"] += br["amp"]
                                found = True
                                break
                        if not found:
                            newbranches.append(br)
                    insertBranch(br0)
                    insertBranch(br1)

            self.branches = newbranches
            self.prune()

            for branch in self.branches:
                if branch[orth.index()] != 0:
                    raise ValueError("Failed to uncompute perpendicular bit.")

            pass

        else:
            raise TypeError("Invalid un-initialization of perpendicular register with type ", type(val))



