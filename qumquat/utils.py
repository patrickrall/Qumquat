from .qvars import *

### Utility functions based on primitive operations
# Guideline: these should not require separate definitions for their inverses,
# but maybe they can inspect the superposition a bit for error checking
class Utils():
    def __init__(self, qq):
        self.qq = qq

    ######################### Casting

    def int(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(expr.c(b))
        newexpr.float = False
        return newexpr

    def float(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: float(expr.c(b))
        newexpr.float = True
        return newexpr

    ######################### Rounding

    def round(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(round(expr.c(b)))
        newexpr.float = False
        return newexpr

    def floor(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(math.floor(expr.c(b)))
        newexpr.float = False
        return newexpr

    def ceil(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(math.ceil(expr.c(b)))
        newexpr.float = False
        return newexpr


    ######################### Trig, sqrt

    def sin(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.sin(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def cos(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.cos(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def tan(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.tan(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def asin(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.asin(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def acos(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.acos(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def atan(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.atan(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def sqrt(self, expr):
        if not isinstance(expr, Expression): expr = Expression(expr)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.sqrt(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    ######################### QRAM

    def qram(self, dictionary, index):
        if not isinstance(index, Expression): index = Expression(index)
        if index.float:
            raise ValueError("QRAM keys must be integers, not floats.")

        # cast dictionaries to lists
        if isinstance(dictionary, list):
            dictionary = {i:dictionary[i] for i in range(len(dictionary))}

        casted_dict = {}

        isFloat = False

        for key in dictionary.keys():
            expr = Expression(dictionary[key])
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
