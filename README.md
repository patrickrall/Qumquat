# Qumquat - Quantum Machine Learning and Quantum Algorithms Toolkit

Qumquat is an experimental high-level quantum programming language. This language is aimed to provide a comfortable environment for experimenting with algorithms like HHL, quantum semidefinite programming, quantum counting, quantum reccomendation systems and quantum convex optimization.  Guiding ideas:

 - These algorithms demand **reversible classical computation in superposition**. Qumquat is designed to feel like any other imperative programming language to make classical programming comfortable.
 - These algorithms do not run on NISQ quantum computers, so **Qumquat never 'compiles' to quantum gates** or even explicitly stores qubits. Since the runtime will always be a classical simulation, infinite-dimensional quantum registers and quantum while loops are possible.
 - Simply implementing an algorithm is an excellent way of solidifying one's understanding and also **ensure that the algorithm behaves as expected**. Qumquat is intended as an **educational tool for all levels of experience** in quantum computation.

Qumquat is a side project that took 1.5 weeks to speed-code. So the documentation and code quality is abysmal, but the basic functionality works.

### Quantum Registers

Quantum registers are created with `qq.reg`. *Qumquat registers are always signed integers*.

The probability distribution of a register can be displayed with `qq.print`.

```python
import qumquat as qq

x = qq.reg(3) # new quantum register with value 3
x += 4

qq.print("My register:", x) # My register: 7.0 w.p. 1.0
```

Multiple registers can be declared at one and printed at once. Pass a list to `qq.reg` and it will initialize the qubit to a superposition of those values.  `qq.print_amp` will list the possible values, and print the amplitudes corresponding to that value.

```python
x,y = qq.reg(10, range(3))

qq.print_amp(x) # 10.0 w.a. 0.57735, 0.57735, 0.57735

qq.print_amp(x,y)
# 10.0 0.0 w.a. 0.57735
# 10.0 1.0 w.a. 0.57735
# 10.0 2.0 w.a. 0.57735

# Watch out for lists with repeated entries:
# z = qq.reg([1,1]) # will raise ValueError

# You can also copy another register
w = qq.reg(y)
```

When you are done with a register you should clean it up, because garbage can mess up the interference pattern your quantum algorithm is creating. To clean up a register, simply guess its value and call `x.clean`.

```python
x,y = qq.reg(10, range(3))
x += 3

x.clean(13) # register x is now deallocated
# x += 1 # raises SyntaxError

z = qq.reg(y)

# y.clean(range(3)) # will fail to uncompute since y is entangled with z
y.clean(z)

z.clean(range(3)) 
```

Operations `+=, -=, *=, //=, **=, ^=, <<=` are permitted whenever they are reversible. Irreversible operations exist as well, but they require the garbage collector.

```python

x = qq.reg(3)

x *= 2    # now x is 6
# x *= 0  # raises IrrevError
x //= 2   # reversible since x is a multiple of 2. x is now 3.
# x // 2  # raises IrrevError now that x is no longer a multiple of 2

x **= 2     # now x is 9
# x **= 0   # raises IrrevError
# x **= -1  # raises IrrevError (x would have to be a float)

x ^= 8   # now x is 1
x <<= 1  # now x is 2
```

#### Expressions

Creating and cleaning a register for every value is cumbersome and inefficient. Sometimes we only need an expression, e.g. `x+2` for a brief moment. When arithmetic on a register is performed, an `Expression` object is created that holds the corresponding value depending on the register. This arithmetic can be irreversible, since the register is not changed. Furthermore expressions can be floats!

```python

x = qq.reg([1,2,3])

qq.print(x*0)  # 0.0 w.p. 1.0

y = qq.reg(x // 2)
qq.print(x,y)
# 1.0 0.0 w.p. 0.33333
# 2.0 1.0 w.p. 0.33333
# 3.0 1.0 w.p. 0.33333

qq.print(x,x / 2)
# 1.0 0.5 w.p. 0.33333
# 2.0 1.0 w.p. 0.33333
# 3.0 1.5 w.p. 0.33333

# DON'T DO THIS! This will not behave as expected.
x = x+1
# Now x is an Expression, not a register.
# You now longer have a reference to the register x used to refer to.
# This bug is nasty since it can be hard to spot. Most qumquat functions
# support running on expressions. One exception is cnot.
x.cnot(0,1) # raises AttributeError
```
If a successor of this language were to compile to a real quantum computer, it would allocate extra qubits to temporarily hold on to the value of the expression. These qubits would then be immediately uncomputed automatically.

#### Measurement

The function `qq.measure` samples a random value from the output distribution and collapses as little of the superposition as necessary.

```python
x = qq.reg([-1,1,-2,2])

out = qq.measure(x**2)
# outputs 1 or 2

qq.print(x)
# outputs either:
# -1.0 w.p. 0.5
# 1.0 w.p. 0.5
# or:
# -2.0 w.p. 0.5
# 2.0 w.p. 0.5
# so the sign stays in superposition!
```

Both `qq.measure` and `qq.print` utilize `qq.distribution`. This is convenient for plotting.

```python
x,y = qq.reg(range(10), range(1,10))

values, probs, branches = qq.distribution(x % y)

# values[i] -> Measurement outcome: a float or a tuple of floats. Maybe strings.
# probs[i] -> Measurement probability.
# branches[i] -> List of superposition branches. Not that useful for users.

import matplotlib.pyplot as plt
plt.bar(values, probs)
plt.show()
```

#### Phase

The `qq.phase(theta)` method allows you to multiply the amplitude `e^(i*theta)`. To make this phase non-global `theta` must be an expression (or you are using a quantum if statement). For your convenience there are `qq.phase_pi(expr)` for `e^(i*pi*expr)` and `qq.phase_2pi(expr)` for `e^(2*pi*i*expr)`.

```python
x = qq.reg(range(3))

qq.phase(1) # this applies an unmeasurable global phase

from math import pi
# these all do the same thing
qq.phase(2*pi*x)
qq.phase_pi(2*x)
qq.phase_2pi(x)
```
 
#### Low level bitwise operations

Qumquat registers are signed integers, not qubits. However in some situations, e.g. graph coloring, it might be more appropriate to view a register as an infinite sequence of qubits. A qumquat register `x` permit access to bits: `x[-1]` is the sign bit and `x[i]` is the 2^i digit in the binary expansion. `x.len()` gives the minumum number of bits needed to write down the register.

```python
x = qq.reg(-10)
qq.print(*[x[i] for i in range(-1,4)])
# 1.0 0.0 1.0 0.0 1.0 w.p. 1.0
# sgn 2^0 2^1 2^2 2^3 
```

Hadamard and CNOT can be perfomed via `x.had(i)` and `x.cnot(ctrl, targ)`.  Qumquat is a high level language - you should not find the need to use Hadamard and CNOT unless you are doing nitty-gritty stuff like implementing QFT or a Grover iterator. 

Example: uniform superposition over all inputs
```python
n = 3

# Don't do this:
x = qq.reg(0)
for i in range(n): qq.had(i)

# Do this instead:
y = qq.reg(range(2**n))
```

Example: Bell state
```python
# Don't do this:
x = qq.reg(0) 
x.had(0)
x.cnot(0,1)

# Do this instead:
y = qq.reg([0,3])
```

Qumquat actually implements a custom class `es_int` - explicitly signed int - for the registers. `es_int` quacks like a regular python int, but +0 and -0 are different numbers, i.e `es_int(0) == -es_int(0)` evaluates to `False`. This is necessary because it should be possible to hadamard the sign bit regardless of the value of the rest of the register. However, this is just a technicality. The user should never have to care, especially since `qq.measure` casts to a float.


### Reversible programming

In classical programming we have many irreversible statements. Quantum computers are reversible, so Qumquat prohibits irreversible programming via some basic rules.

1. A statement cannot depend on the value of its target register. This prohibits `x ^= x` for example.
2. A controlling register cannot be the target of a statement.  See below for an example.

The quantum garbage collector lets you violate these rules, but let's first discuss reversible control flow.

#### If statements

Use `with qq.q_if(expr):` to perform statements only when `expr != 0`.

```python
x,y = qq.reg(range(3), 0)

with qq.q_if(x > 1): y += x 

qq.print(x,y)
# 0.0 0.0 w.p. 0.33333
# 1.0 0.0 w.p. 0.33333
# 2.0 2.0 w.p. 0.33333

# with qq.q_if(x > 1): x -= 1  # raises SyntaxError

# Z gate on index 1
if qq.q_if(x[1]): qq.phase_pi(1)
```

Quantum if statements do not affect register creation.

```python
x = qq.reg([0,1])
with qq.q_if(x): y = qq.reg(2)
qq.print(y)
# 2.0 w.p. 1.0
```

#### Inversion

To run a sequence of statements in reverse you can use `with qq.inv():`. For example, let's implement a QFT adder - a simple but inefficient technique for modular addition.

```python

def omega(x, n):
    qq.phase_2pi(x/(2**n))

def qft(x,n):
     for i in range(n)[::-1]:
        x.had(i)
        with qq.q_if(x[i]):
            omega((x % 2**i)*2**(n-i-1),n)

    # reverse order
    for i in range(n//2):
        x.cnot(i,n-i-1)
        x.cnot(n-i-1,i)
        x.cnot(i,n-i-1)

# add 3 modulo 8
n = 3

x_prv = qq.reg([1,5,7])
x = qq.reg(x_prv)
qft(x,n)
omega(3*x, n)
with qq.inv(): qft(x,n) # inverse QFT

qq.print(x_prv, x)
# 1.0 4.0 w.p. 0.33333
# 5.0 0.0 w.p. 0.33333
# 7.0 2.0 w.p. 0.33333
```

Inversion interacts more interestingly with `qq.reg` - the inverse of of `x = qq.reg(42)` is `x.clean(42)`. But if you only write `qq.reg` without a matching `clean`, then inverted `qq.reg` will deallocate ... what register?

```python
x = qq.reg(0)

with qq.inv():
    y = qq.reg(3)
    x += y
    y.clean(3)
    
qq.print(x)
# -3.0 w.p. 1.0

# with qq.inv():
#     z = qq.reg(2)
# raises SyntaxError -> attempted to read register that was never allocated.
# z = qq.reg(2) is inverted to z.clean(2), but z is unallocated.
```

So how does one uncompute garbage? This situation is unsatisfying because it encourages you to factor out your garbage registers as shown below. The quantum garbage collector makes this unnecessary.

```python
def do_thing(x, tmp):
    tmp += x**2
    x += tmp
    
x = qq.reg(range(4))
tmp = qq.reg(0)  # scratch space for do_thing

do_thing(x,tmp)
out = qq.reg(x)
with qq.inv(): do_thing(x,tmp)

tmp.clean(0) # scratch space is uncomputed

qq.print(x,out)
# 0.0 0.0 w.p. 0.25
# 1.0 2.0 w.p. 0.25
# 2.0 6.0 w.p. 0.25
# 3.0 12.0 w.p. 0.25
```

#### While Loops

Quantum while `qq.q_while(cond, tmp)` loops demand not only a loop condition `cond`, but also a temporary variable `tmp` to store the number of loops. This variable can't be changed in the while loop or affect the loop condition.

On a real quantum computer a while loop is only possible if an upper bound on the number of iterations is known - how else would you generate the quantum circuit? Qumquat's simulator saves you this inconvenience by introspecting the superposition and stopping the loop when all branches are done.

```python
x, y = qq.reg([2,3,4], 0)
i, tmp = qq.reg(0,0)

# goal:
# for i in range(x): y += i**2

with qq.q_while(i < x, tmp):
    y += i**2
    i += 1

qq.print(x,y,i,tmp)
# 2.0 1.0 2.0 2.0 w.p. 0.25
# 3.0 5.0 3.0 3.0 w.p. 0.25
# 4.0 14.0 4.0 4.0 w.p. 0.25
# 5.0 30.0 5.0 5.0 w.p. 0.25

# since x = i = tmp we can uncompute i and tmp
i.clean(x)
tmp.clean(x)
```

Since for loops are just while loops in disguise, let's implement a for loop. Python's `with` statement calls the `__enter__` and `__exit__` methods before and after the code block respectively.

```python

class q_for():
    def __init__(self, i, maxval):
        self.i = i
        self.tmp = qq.reg(0) # temporary register
        self.i_start = qq.reg(i) # copy the initial value
        self.maxval = maxval
        self.q_while = qq.q_while(i < maxval, self.tmp)

    def __enter__(self):
        self.q_while.__enter__()

    def __exit__(self, *args):
        self.i += 1
        self.q_while.__exit__()

        # clean the temporary register
        self.tmp.clean(self.i - self.i_start)

        self.i -= self.maxval      # empty the i register
        self.i += self.i_start     # fill with i_start
        self.i_start.clean(self.i) # clean i_start



x = qq.reg([3,4,5])
out = qq.reg(0)

i = qq.reg(3)
with q_for(i, x):
    out += i**2

qq.print(x,out,i)
# 3.0 0.0 3.0 w.p. 0.33333
# 4.0 9.0 3.0 w.p. 0.33333
# 5.0 25.0 3.0 w.p. 0.33333
```

### Quantum Garbage Collection

