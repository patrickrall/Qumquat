from .qvars import *
from random import random
import math, copy, cmath

# these modules export a class M, short for Mixin
from .keys import Keys
from .init import Init
from .measure import Measure
from .control import Control
from .garbage import Garbage
from .primitive import Primitive
from .perp import Perp
from .utils import Utils
from .snapshots import Snapshots

# - queue_action, queue_stack
# - call (inversion, controls)
# - assert_mutable
# - controlled_branches
# - key_count, reg_count, key_dict
# - pile_stack, garbage_piles, garbage_stack
# - push_mode, pop_mode, mode_stack

class Qumquat(Keys, Init, Measure, Control, Primitive, Perp, Utils, Snapshots, Garbage):
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

    thresh = 1e-10 # threshold for deleting tiny amplitudes

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
