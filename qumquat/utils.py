from .qvars import *

# utils.py
#  - int, float, round, floor, ceil
#  - trig, sqrt
#  - qram
#  - swap

class Utils:

######################### Casting

    def int(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return int(expr)
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(expr.c(b))
        newexpr.float = False
        return newexpr

    def float(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return float(expr)
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: float(expr.c(b))
        newexpr.float = True
        return newexpr

######################### Rounding

    def round(self, expr):
        if not isinstance(expr, Expression):
            if hasattr(expr, "__round__"): return round(expr)
            expr = Expression(expr, qq=self)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(round(expr.c(b)))
        newexpr.float = False
        return newexpr

    def floor(self, expr):
        if not isinstance(expr, Expression):
            if hasattr(expr, "__floor__"): return floor(expr)
            expr = Expression(expr, qq=self)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(math.floor(expr.c(b)))
        newexpr.float = False
        return newexpr

    def ceil(self, expr):
        if not isinstance(expr, Expression):
            if hasattr(expr, "__ceil__"): return ceil(expr)
            expr = Expression(expr, qq=self)
        if not expr.float: return expr

        newexpr = Expression(expr)
        newexpr.c = lambda b: es_int(math.ceil(expr.c(b)))
        newexpr.float = False
        return newexpr


######################### Trig, sqrt

    def sin(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.sin(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.sin(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def cos(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.cos(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.cos(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def tan(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.tan(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.tan(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def asin(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.asin(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.asin(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def acos(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.acos(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.acos(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def atan(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.atan(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.atan(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def sqrt(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.sqrt(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.sqrt(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    def exp(self, expr):
        if not isinstance(expr, Expression):
            if not isinstance(expr, Key): return math.exp(float(expr))
            expr = Expression(expr, qq=self)
        newexpr = Expression(expr)
        newexpr.c = lambda b: math.exp(float(expr.c(b)))
        newexpr.float = True
        return newexpr

    ######################### QRAM

    def qram(self, dictionary, index):
        if not isinstance(index, Expression): index = Expression(index, qq=self)
        if index.float:
            raise ValueError("QRAM keys must be integers, not floats.")

        # cast dictionaries to lists
        if isinstance(dictionary, list):
            dictionary = {i:dictionary[i] for i in range(len(dictionary))}

        casted_dict = {}

        isFloat = False

        for key in dictionary.keys():
            expr = Expression(dictionary[key], qq=self)
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


