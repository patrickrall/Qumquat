from .qvars import *
import cmath

# keys.py:
#  - clear
#  - prune
#  - alloc
#  - reg
#  - clean
#  - expr

class Keys:

    ############################ Clear and prune

    # delete all variables and start anew
    def clear(self):
        if len(self.controls) > 0 or len(self.queue_stack) > 0 or\
                len(self.garbage_stack) > 0 or len(self.mode_stack) > 0:
            raise SyntaxError("Cannot clear inside quantum control flow.")

        self.key_dict = {}

        self.pile_stack = []
        self.garbage_piles = {"keyless": []}
        self.garbage_stack = []
        self.branches = [{"amp": 1+0j}]

    # get rid of branches with tiny amplitude
    def prune(self):
        newbranches = []
        norm = 0

        for branch in self.branches:
            if abs(branch["amp"]) > self.thresh:
                newbranches.append(branch)
                norm += abs(branch["amp"])**2
        norm = cmath.sqrt(norm)

        self.branches = newbranches
        for branch in self.branches:
            branch["amp"] /= norm


    ############################ Alloc and dealloc

    def alloc(self, key):
        if self.queue_action('alloc', key): return
        self.assert_mutable(key)

        reg = self.reg_count
        self.key_dict[key.key].append(reg)
        self.reg_count += 1

        for branch in self.branches: branch[reg] = es_int(0)


    def alloc_inv(self, key):
        if self.queue_action('alloc_inv', key): return
        self.assert_mutable(key)

        if key.allocated(): # this is just a regular key deallocation
            target = key
            proxy = None
        else: # we are the proxy for another key
            target = key.partner()
            proxy = key

        # remove the register from the branches and key_dict
        for branch in self.branches: branch.pop(target.index())
        self.key_dict[target.key].remove(target.index())

        pile = key.pile()

        if not target.allocated() and pile is not None:
            # remove proxy if it exists
            if proxy is not None:
                for i in range(len(pile)):
                    if pile[i].key == proxy.key:
                        del pile[i]
                        break

            # remove target
            for i in range(len(pile)):
                if pile[i].key == target.key:
                    del pile[i]
                    break

    ########################### User functions for making and deleting registers

    def reg(self, *vals):
        out = []
        for val in vals:
            key = Key(self)
            out.append(key)

            # this is not in alloc because it pertains to keys, not registers
            if len(self.pile_stack_py) > 0:
                self.pile_stack_py[-1].append(key)

            self.alloc(key)
            self.init(key, val)

        if len(out) > 1: return tuple(out)
        else: return out[0]


    def clean(self, key, val):
        self.init_inv(key, val)
        self.alloc_inv(key)

    def expr(self, val):
        return Expression(val, self)

