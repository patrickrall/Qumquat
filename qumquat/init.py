from .qvars import *
import math, copy

class Init:

    ############################ Base routines

    def init(self, key, val):
        if self.queue_action('init', key, val): return
        self.assert_mutable(key)

        # cast ranges to superpositions, permitting qq.reg(range(3))
        if isinstance(val, range): val = list(val)
        if isinstance(val, Key): val = Expression(val)
        if isinstance(val, int) or isinstance(val, es_int): val = Expression(val, self)

        if isinstance(val, Expression):
            self.init_expression(key,val)
        elif isinstance(val, list):
            self.init_list(key,val)
        elif isinstance(val, dict):
            self.init_dict(key,val)
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

        if isinstance(val, Expression):
            self.init_expression(key,val,invert=True)
        elif isinstance(val, list):
            self.init_list(key,val,invert=True)
        elif isinstance(val, dict):
            self.init_dict(key,val,invert=True)
        else:
            raise TypeError("Invalid un-initialization of register with type ", type(val))

    ############################ Expression

    def init_expression(self,key,expr, invert=False):
        if expr.float: raise TypeError("Quantum registers can only contain ints")
        if key.key in expr.keys: raise SyntaxError("Can't initialize register based on itself.")

        # strategy:
        # for each value of expr, create a list [0,expr,other,initial,vals]
        # then the unitary simply shifts forward by one

        H = set([b[key.index()] for b in self.controlled_branches()]) - set([es_int(0)])

        for b in self.controlled_branches():
            v = es_int(expr.c(b))
            if v != es_int(0): # if already zero do nothing

                thisH = [es_int(0),v] + sorted(list(H - set([v])))

                idx = thisH.index(b[key.index()])
                if not invert:
                    b[key.index()] = thisH[(idx + 1) % len(thisH)]
                else:
                    b[key.index()] = thisH[(len(thisH) + idx - 1) % len(thisH)]


    ############################ List

    def init_list(self,key,ls, invert=False):
        # check list for validity, cast to es_int
        for i in range(len(ls)):
            if not (isinstance(ls[i], int) or isinstance(ls[i], es_int)):
                raise TypeError("Superpositions only support integer literals.")
            if ls.index(ls[i]) != i:
                raise ValueError("Superpositions can't contain repeated values.")
            if isinstance(ls[i], int):
                ls[i] = es_int(ls[i])

        p = 1/math.sqrt(len(ls))
        H = (set([b[key.index()] for b in self.controlled_branches()]) | set(ls)) - set([es_int(0)])
        H = [es_int(0)] + list(H)

        U = [{h:complex(p if (h in ls) else 0) for h in H}] # first column of U

        # complete the rest of the matrix via graham schmidt
        for i in H[1:]+H[:1]: # this way its closer to the identity
            newcol = {h:complex(1 if (h == i) else 0) for h in H}
            for col in U:
                inner = sum([col[h].conjugate()*newcol[h] for h in H])
                for h in H: newcol[h] -= col[h]*inner

            # normalize
            norm = math.sqrt(sum([abs(newcol[h])**2 for h in H]))
            if norm < self.thresh: continue
            for h in H: newcol[h] /= norm
            U.append(newcol)

        if len(U) != len(H): raise ValueError("Error in matrix completion. (This can happen when amplitudes get too small.)")

        if invert:
            newU = []
            for i in H:
                newU.append({h:(U[H.index(h)][i].conjugate()) for h in H})

            U = newU

        newbranches = []

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        for b in self.branches:
            if not goodbranch(b):
                newbranches.append(b)
                continue

            row = U[H.index(b[key.index()])]
            for h in H:
                if abs(row[h]) != 0:
                    newbranch = copy.copy(b)
                    newbranch[key.index()] = h
                    newbranch["amp"] *= row[h]
                    newbranches.append(newbranch)

        self.branches = newbranches
        self.prune()



    ############################ Dictionary

    def init_dict(self,key,dic,invert=False):
        # check if dictionary has integer keys, cast to es_int
        newdic = {}
        keys = set([])
        for k in dic.keys():
            if not isinstance(k, int): raise TypeError("QRAM keys must be integers.")
            newdic[es_int(k)] = Expression(dic[k], qq=self)
            keys |= newdic[es_int(k)].keys
        dic = newdic

        if key.key in keys: raise SyntaxError("Can't initialize register based on itself.")

        keys = [Key(self,val=k) for k in keys]


        ############## sort branches into groups with equal value

        def branchesEqual(b1, b2):
            for k in keys:
                if self.branches[b1][k.index()] != self.branches[b2][k.index()]:
                    return False
            return True

        branch_type_counter = 0
        branchtypes = {}

        goodbranch = lambda b: all([ctrl.c(b) != 0 for ctrl in self.controls])
        for i in range(len(self.branches)):
            b = self.branches[i]
            if not goodbranch(b): continue

            found = False
            for j in branchtypes:
                if branchesEqual(branchtypes[j][0], i):
                    found = True
                    branchtypes[j].append(i)
                    break

            if not found:
                branchtypes[branch_type_counter] = [i]
                branch_type_counter += 1
                continue


        ############ determine unitary for each group

        H = set([b[key.index()] for b in self.controlled_branches()])
        H = (H | set(dic.keys())) - set([es_int(0)])
        H = [es_int(0)] + list(H)

        unitaries = []

        for j in range(branch_type_counter):
            norm = 0
            for k in dic.keys(): norm += abs( dic[k].c(self.branches[branchtypes[j][0]]) )**2
            norm = math.sqrt(norm)

            U = [{h:(dic[h].c(self.branches[branchtypes[j][0]])/norm\
                    if h in dic.keys() else complex(0)) for h in H}]

            # complete the rest of the matrix via graham schmidt
            for i in H[1:]+H[:1]: # this way its closer to the identity
                newcol = {h:complex(1 if (h == i) else 0) for h in H}
                for col in U:
                    inner = sum([col[h].conjugate()*newcol[h] for h in H])
                    for h in H: newcol[h] -= col[h]*inner

                # normalize
                norm = math.sqrt(sum([abs(newcol[h])**2 for h in H]))
                if norm < self.thresh: continue
                for h in H: newcol[h] /= norm
                U.append(newcol)


            if len(U) != len(H): raise ValueError("Error in matrix completion. (This can happen when amplitudes get too small.)")

            if invert:
                newU = []
                for i in H:
                    newU.append({h:(U[H.index(h)][i].conjugate()) for h in H})

                unitaries.append(newU)
            else:
                unitaries.append(U)

        ########### apply unitary

        newbranches = []
        for i in range(len(self.branches)):
            b = self.branches[i]
            if not goodbranch(b):
                newbranches.append(b)
                continue

            for j in range(branch_type_counter):
                if i in branchtypes[j]: break

            U = unitaries[j]
            row = U[H.index(b[key.index()])]
            for h in H:
                if abs(row[h]) != 0:
                    newbranch = copy.copy(b)
                    newbranch[key.index()] = h
                    newbranch["amp"] *= row[h]
                    newbranches.append(newbranch)

        self.branches = newbranches
        self.prune()

