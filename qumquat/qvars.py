import math
import inspect

# explicitly signed int
class es_int(object):

    def __init__(self, val):
        if isinstance(val, es_int):
            self.sign = val.sign
            self.mag = val.mag
        elif isinstance(val, int):
            self.sign = -1 if val < 0 else 1
            self.mag = abs(val)
        elif isinstance(val, float):
            self.sign = -1 if "-" in str(val) else 1
            self.mag = int(abs(val))
        else: raise TypeError

    def __add__(self, expr): return es_int(int(self) + int(expr))
    def __sub__(self, expr): return es_int(int(self) - int(expr))
    def __mul__(self, expr): return es_int(int(self) * int(expr))

    def __radd__(self, expr): return self + expr
    def __rsub__(self, expr): return -self + expr
    def __rmul__(self, expr): return self * expr

    def __truediv__(self, expr): return float(self) / float(expr)
    def __floordiv__(self, expr): return es_int(int(self) // int(expr))
    def __mod__(self, expr): return es_int(int(self) % int(expr))

    def __rtruediv__(self, expr): return float(expr) / float(self)
    def __rfloordiv__(self, expr): return es_int(int(expr) // int(self))
    def __rmod__(self, expr): return es_int(int(expr) % int(self))

    def __pow__(self, expr, *modulo):
        if not isinstance(expr, int) and not isinstance(expr, es_int):
            raise TypeError("Pow only supported for integers. Cast to float first.")
        return es_int(pow(int(self),int(expr),*modulo))

    def __rpow__(self, expr): return pow(es_int(expr), self)

    # defined on the magnitude, but preserves sign
    def __lshift__(self, expr): return es_int(self.sign*(int(abs(self)) << int(expr)))
    def __rshift__(self, expr): return es_int(self.sign*(int(abs(self)) >> int(expr)))

    def __rlshift__(self, expr): return es_int(self.sign*(int(abs(expr)) << int(self)))
    def __rrshift__(self, expr): return es_int(self.sign*(int(abs(expr)) >> int(self)))

    # defined on the magnitude, always unsigned
    def __and__(self, expr): return es_int(self.mag & abs(int(expr)))
    def __xor__(self, expr):
        expr = es_int(expr)
        return es_int(self.mag ^ expr.mag) * self.sign * expr.sign
    def __or__(self, expr): return es_int(self.mag | abs(int(expr)))

    def __rand__(self, expr): return self & expr
    def __rxor__(self, expr): return self ^ expr
    def __ror__(self, expr): return self | expr

    def __neg__(self):
        out = es_int(self)
        out.sign *= -1
        return out
    def __abs__(self): return es_int(self.mag)

    def __complex__(self): return complex(self.sign * self.mag)
    def __int__(self): return self.sign * self.mag
    def __float__(self): return float(self.sign * self.mag)

    # For example: for i in range(-1, len(x)): print(x)
    def __len__(self):
        i = 0
        while 2**i <= self.mag: i += 1
        return i

    def __bool__(self):
        return self.mag > 0

    def __getitem__(self, index):
        if index == -1: # -1 is sign bit
            return es_int(1 if self.sign == -1 else 0)
        else:
            return es_int(1 if (self.mag & (1 << index)) else 0)

    def __setitem__(self, key, value):
        key = int(key)
        if key < -1: raise IndexError

        if self[key] == (int(value) % 2): return
        if key == -1:
            self.sign *= -1
            return

        if self[key]:
            self.mag -= 2**key
            if self.mag < 0:
                self.mag = abs(self.mag)
                self.sign *= -1
        else:
            self.mag += 2**key

    def __repr__(self): return str(self)
    def __str__(self): return ("+" if self.sign > 0 else "-") + str(int(self.mag))

    def __lt__(self, expr): return int(self) < int(expr)
    def __le__(self, expr): return int(self) <= int(expr)
    def __gt__(self, expr): return int(self) > int(expr)
    def __ge__(self, expr): return int(self) >= int(expr)

    def __eq__(self, expr):
        expr = es_int(expr)
        return self.mag == expr.mag and self.sign == expr.sign

    def __round__(self): return self

    # hashable
    def __hash__(self):
        return self.mag*2 + (1 if self.sign == 1 else 0)


#####################################

class IrrevError(Exception):
    pass

def callPath():
    frame = inspect.currentframe().f_back.f_back
    return "File " + frame.f_code.co_filename + ", line "+ str(frame.f_lineno)

def irrevError(x, cond, path):
    if cond: raise IrrevError("Specified operation is not reversible. ("+path+")")
    return x

####################################

class Key():
    def __init__(self, qq, val=None):
        self.qq = qq


        if val is None:
            self.key = qq.key_count
            qq.key_count += 1
            qq.key_dict[self.key] = None
        else:
            self.key = val
        self.partnerCache = None

    def __repr__(self):
        status = "unallocated"
        if self.allocated(): status = "allocated"
        return "<Qumquat Key: "+str(self.key)+", "+status+">"

    def allocated(self):
        return self.qq.key_dict[self.key] is not None

    # for debug - print short identifying string
    def short(self):
        status = "u"
        if self.allocated(): status = "a"
        return str(self.key)+status

    def pile(self):
        for pile in self.qq.pile_stack_qq:
            if any([self.key == key.key for key in pile]):
                return pile
        return None

    def partner(self):
        if self.allocated(): return self
        else:
            if self.partnerCache is not None:
                return self.partnerCache

            pile = self.pile()
            if pile is None:
                raise SyntaxError("Attempted to read un-allocated key.")

            i = 0 # partner index
            for key in pile:
                if key.key == self.key: break
                if key.allocated(): continue
                i += 1

            if not pile[i].allocated():
                raise SyntaxError("Garbage collector error: ran out of registers to uncompute.")

            self.partnerCache = pile[i]
            return pile[i]


    def index(self):
        if not self.allocated():
            partner = self.partner()
            return self.partner().index()

        return self.qq.key_dict[self.key]

    ############################ operations (a + b) forward to expressions

    def __add__(self, expr): return Expression(self) + expr
    def __radd__(self, expr): return expr + Expression(self)

    def __sub__(self, expr): return Expression(self) - expr
    def __rsub__(self, expr): return expr - Expression(self)

    def __mul__(self, expr): return Expression(self) * expr
    def __rmul__(self, expr): return expr * Expression(self)

    def __truediv__(self, expr): return Expression(self) / expr
    def __rtruediv__(self, expr): return expr / Expression(self)

    def __floordiv__(self, expr): return Expression(self) // expr
    def __rfloordiv__(self, expr): return expr // Expression(self)

    def __mod__(self, expr): return Expression(self) % expr
    def __rmod__(self, expr): return expr % Expression(self)

    def __pow__(self, expr): return pow(Expression(self), expr)
    def __rpow__(self, expr): return pow(expr, Expression(self))

    def __and__(self, expr): return Expression(self) & expr
    def __rand__(self, expr): return expr & Expression(self)

    def __xor__(self, expr): return Expression(self) ^ expr
    def __rxor__(self, expr): return expr ^ Expression(self)

    def __or__(self, expr): return Expression(self) | expr
    def __ror__(self, expr): return expr | Expression(self)

    def __neg__(self): return -Expression(self)
    def __abs__(self): return abs(Expression(self))

    def __lshift__(self, expr): return Expression(self) << expr
    def __rshift__(self, expr): return Expression(self) >> expr

    def __rlshift__(self, expr): return expr << Expression(self)
    def __rrshift__(self, expr): return expr >> Expression(self)


    def __complex__(self): return complex(Expression(self))
    def __int__(self): return int(Expression(self))
    def __float__(self): return float(Expression(self))

    def len(self): return Expression(self).len()
    def __getitem__(self, index): return Expression(self)[index]

    def __lt__(self, expr): return Expression(self) < expr
    def __le__(self, expr): return Expression(self) <= expr
    def __gt__(self, expr): return Expression(self) > expr
    def __ge__(self, expr): return Expression(self) >= expr
    def __eq__(self, expr): return Expression(self) == expr
    def __ne__(self, expr): return Expression(self) != expr

    # Use qq.round(expr), etc.
    # def round(self): Expression(self).round()
    # def floor(self): Expression(self).floor()
    # def ceil(self): Expression(self).ceil()

    ##################################  statements (a += b) forward to qq.op()

    def __iadd__(self, expr):
        expr = Expression(expr, self.qq)
        if expr.float: raise ValueError("Can't add float to register.")
        do = lambda b: b[self.index()] + expr.c(b)
        undo = lambda b: b[self.index()] - expr.c(b)
        self.qq.oper(self, expr, do, undo)
        return self

    def __isub__(self, expr):
        expr = Expression(expr, self.qq)
        if expr.float: raise ValueError("Can't subtract float from register.")
        do = lambda b: b[self.index()] - expr.c(b)
        undo = lambda b: b[self.index()] + expr.c(b)
        self.qq.oper(self, expr, do, undo)
        return self

    def __imul__(self, expr):
        path = callPath()
        expr = Expression(expr, self.qq)
        if expr.float: raise ValueError("Can't multiply register by float.")
        do = lambda b: b[self.index()] * irrevError(expr.c(b), expr.c(b) == 0, path)
        undo = lambda b: irrevError(b[self.index()] // expr.c(b), b[self.index()] % expr.c(b) != 0, path)
        self.qq.oper(self, expr, do, undo)
        return self

    def __itruediv__(self, expr):
        raise SyntaxError("True division might make register a float. Use floor division: //=")

    def __ifloordiv__(self, expr):
        path = callPath()
        expr = Expression(expr, self.qq)
        do = lambda b: irrevError(b[self.index()] // expr.c(b), b[self.index()] % expr.c(b) != 0, path)
        undo = lambda b: b[self.index()] * irrevError(expr.c(b), expr.c(b) == 0, path)
        self.qq.oper(self, expr, do, undo)
        return self

    def __ixor__(self, expr):
        expr = Expression(expr, self.qq)
        do = lambda b: b[self.index()] ^ expr.c(b)
        self.qq.oper(self, expr, do, do)
        return self

    def __ipow__(self, expr):
        path = callPath()
        expr = Expression(expr, self.qq)

        def check(b):
            if expr.float: return True
            v = expr.c(b)
            if int(v) != v: return True  # fractional powers create floats
            if v <= 0: return True       # negative powers create floats, 0 power is irreversible
            return False

        def check_inv(b):
            if expr.float: return True
            v = expr.c(b)
            if int(v) != v: return True  # fractional powers create floats
            if v <= 0: return True       # negative powers create floats, 0 power is irreversible
            out = float(b[self.index()])**float(1/v)
            if int(out) != out: return True # must be a perfect square
            return False

        do = lambda b: irrevError((b[self.index()]**(expr.c(b))),  check(b), path)
        undo = lambda b: irrevError(es_int(int(b[self.index()])**(1/expr.c(b))), check_inv(b), path)

        self.qq.oper(self, expr, do, undo)
        return self


    def __ilshift__(self, expr):
        expr = Expression(expr, self.qq)

        do = lambda b: b[self.index()] << expr.c(b)
        undo = lambda b: b[self.index()] >> expr.c(b)

        self.qq.oper(self, expr, do, undo)
        return self




    ######################### Irreversible operations

    def assert_garbage(self, op):
        if len(self.qq.pile_stack_py) == 0:
            raise SyntaxError("Need garbage collector to perform irreversible operation "+op+".")

    def assign(self, value):
        self.assert_garbage("assign")
        diff = self.qq.reg(value - self)
        self += diff

    def __setitem__(self, key, value):
        self.assert_garbage("setitem")
        value = value % 2

        if key == -1: self.assign(-self*(self[key] != value))
        else: self.assign(self + (1 - 2*self[-1])*(value - self[key])*2**key)
        return self

    def __imod__(self, expr):
        self.assert_garbage("modset")
        self.assign(self % expr)
        return self

    def __irshift__(self, expr):
        self.assert_garbage("rshiftset")
        self.assign(self >> expr)
        return self

    def __iand__(self, expr):
        self.assert_garbage("andset")
        self.assign(self & expr)
        return self

    def __ior__(self, expr):
        self.assert_garbage("orset")
        self.assign(self | expr)
        return self

    ######################### Shortcuts

    def qft(self, d):
        self.qq.qft(self, d)

    def had(self, idx):
        self.qq.had(self, idx)

    def cnot(self, idx1, idx2):
        self.qq.cnot(self, idx1, idx2)

    def clean(self, expr):
        self.qq.clean(self, expr)

    def init(self, val):
        self.qq.init(self, val)

    def perp(self, val):

        class WrapPerp():
            def __enter__(s):
                s.bit = self.qq.reg(0)

                with self.qq.inv(): self.init(val)
                with self.qq.control(self != 0): s.bit += 1
                self.init(val)

                return Expression(s.bit)

            def __exit__(s, *args):
                with self.qq.inv(): self.init(val)
                with self.qq.control(self != 0): s.bit -= 1
                self.init(val)

                s.bit.clean(0)

        return WrapPerp()

###################################################################

# Holds onto lambda expressions that are functions of
# quantum registers (which are always es_int). Can be either int or float.

class Expression(object):
    def __init__(self, val, qq=None):
        if isinstance(val, Expression):
            self.keys = val.keys
            self.c = val.c
            self.float = val.float
            qq = val.qq

        if isinstance(val, Key):
            self.keys = set([val.key])
            self.c = lambda b: b[val.index()]
            self.float = False
            qq = val.qq

        if qq is None: raise ValueError
        self.qq = qq

        if isinstance(val, int) or isinstance(val, es_int):
            self.keys = set([])
            self.c = lambda b: es_int(val)
            self.float = False

        if isinstance(val, float):
            self.keys = set([])
            self.c = lambda b: val
            self.float = True

        if not hasattr(self, "keys"):
            raise ValueError("Invalid expression of type " + str(type(val)))

    # private method
    def op(self, expr, c, floatmode="inherit"):
        # "inherit" -> is float if any parent is float
        # "always" -> always a float
        # "never" -> never a float

        expr = Expression(expr, self.qq)

        newexpr = Expression(0, self.qq)
        newexpr.keys = set(self.keys) | set(expr.keys)

        if floatmode == "inherit":
             newexpr.float = self.float or expr.float
        if floatmode == "always": newexpr.float = True
        if floatmode == "never": newexpr.float = False

        if newexpr.float:
            newexpr.c = lambda b: c(float(self.c(b)), float(expr.c(b)))
        else:
            newexpr.c = lambda b: c(self.c(b), expr.c(b))

        return newexpr

    def __add__(self, expr): return self.op(expr, lambda x,y: x+y)
    def __sub__(self, expr): return self.op(expr, lambda x,y: x-y)
    def __mul__(self, expr): return self.op(expr, lambda x,y: x*y)

    def __radd__(self, expr): return self + expr
    def __rsub__(self, expr): return -self + expr
    def __rmul__(self, expr): return self * expr

    def __truediv__(self, expr): return self.op(expr, lambda x,y: x / y, "always")
    def __floordiv__(self, expr): return self.op(expr, lambda x,y: x // y)
    def __mod__(self, expr): return self.op(expr, lambda x,y: x % y)

    def __rtruediv__(self, expr): return self.op(expr, lambda x,y: y / x, "always")
    def __rfloordiv__(self, expr): return self.op(expr, lambda x,y: y // x)
    def __rmod__(self, expr): return self.op(expr, lambda x,y: y % x)

    def __pow__(self, expr): return self.op(expr, lambda x,y: x**y, "always")
    def __rpow__(self, expr): return pow(Expression(expr, self.qq), self)

    def __neg__(self):
        newexpr = Expression(self)
        newexpr.c = lambda b: -(self.c(b))
        return newexpr
    def __abs__(self):
        newexpr = Expression(self)
        newexpr.c = lambda b: abs(self.c(b))
        return newexpr

    ######################### Bitwise operations

    def __lshift__(self, expr): return self.op(expr, lambda x,y: x << y, "never")
    def __rshift__(self, expr): return self.op(expr, lambda x,y: x >> y, "never")
    def __and__(self, expr): return self.op(expr, lambda x,y: x & y, "never")
    def __xor__(self, expr): return self.op(expr, lambda x,y: x ^ y, "never")
    def __or__(self, expr): return self.op(expr, lambda x,y: x | y, "never")

    def __rlshift__(self, expr): return self.op(expr, lambda x,y: y << x, "never")
    def __rrshift__(self, expr): return self.op(expr, lambda x,y: y >> x, "never")
    def __rand__(self, expr): return self & expr
    def __rxor__(self, expr): return self ^ expr
    def __ror__(self, expr): return self | expr


    ######################### Getting bit values

    def len(self):
        if self.float: raise TypeError("Bit representations of floats not supported.")
        newexpr = Expression(self)
        newexpr.c = lambda b: es_int(len(self.c(b)))
        newexpr.float = False
        return newexpr

    def __getitem__(self, index):
        if self.float: raise TypeError("Bit representations of floats not supported.")
        newexpr = self.op(index, lambda x,y: x[y], False)
        newexpr.float = False
        return newexpr

   ######################### Comparisons

    # should return int
    def __lt__(self, expr): return self.op(expr, lambda x,y: es_int(x < y), "never")
    def __le__(self, expr): return self.op(expr, lambda x,y: es_int(x <= y), "never")
    def __gt__(self, expr): return self.op(expr, lambda x,y: es_int(x > y), "never")
    def __ge__(self, expr): return self.op(expr, lambda x,y: es_int(x >= y), "never")
    def __eq__(self, expr): return self.op(expr, lambda x,y: es_int(x == y), "never")
    def __ne__(self, expr): return self.op(expr, lambda x,y: es_int(x != y), "never")
