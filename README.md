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

Creating and cleaning a register for every value is cumbersome and inefficient. Sometimes we only need an expression, e.g. `x+2` for a brief moment. When arithmetic on a register is performed, an `Expression` object is created that holds the corresponding value depending on the register. This arithmetic can be irreversible, since the register is not changed.

```python

x = qq.reg([1,2,3])

qq.print(x*0)  # 0.0 w.p. 1.0

y = qq.reg(x // 2)
qq.print(x,y)
# 1.0 0.0 w.p. 0.33333
# 2.0 1.0 w.p. 0.33333
# 3.0 1.0 w.p. 0.33333

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

#### Low level operations


### Reversible programming

#### Inversion

#### Basic rules

#### If statements


#### While Loops

### Quantum Garbage Collection

