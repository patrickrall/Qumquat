from qvars import *

### Utility functions based on primitive operations
# Guideline: these should not require separate definitions for their inverses,
# but maybe they can inspect the superposition a bit for error checking
class Utils():
    def __init__(self, qq):
        self.qq = qq

    def swap(self, key1, key2):
        key1 -= key2 # a1 = a0-b0
        key2 += key1 # b1 = b0+a1 = a0
        key1 -= key2 # a2 = a1-b1 = -b0
        key1 *= -1

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
