# Qumquat
## Quantum Machine Learning and Quantum Algorithms Toolkit

Qumquat is an experimental high-level quantum programming language. This language is aimed to provide a comfortable environment for experimenting with algorithms like HHL, quantum semidefinite programming, quantum counting, quantum reccomendation systems and quantum convex optimization.  Guiding ideas:

 - These algorithms demand **reversible classical computation in superposition**. Qumquat is designed to feel like any other imperative programming language to make classical programming comfortable.
 - These algorithms do not run on NISQ quantum computers, so **Qumquat never 'compiles' to quantum gates** or even explicitly stores qubits. Since the runtime will always be a classical simulation, infinite-dimensional quantum registers are possible.
 - Simply implementing an algorithm is an excellent way of solidifying one's understanding and also to ensure that the algorithm behaves as expected. Qumquat is intended as an educational tool for all levels of experience in quantum computation.

To install, clone into the git repository, then install using pip:
```
git clone git@github.com:patrickrall/Qumquat.git
cd Qumquat
pip install -e .
```
Then you can use `import qumquat as qq` anywhere.

## Quantum Registers

Quantum registers are created with `qq.reg`. **Qumquat registers are always signed integers**.

The probability distribution of a register can be displayed with `qq.print`.

```python
import qumquat as qq

x = qq.reg(3) # new quantum register with value 3
x += 4

qq.print("My register:", x) # My register: 7.0 w.p. 1.0
```

Pass a list to `qq.reg` to create an even superposition over the integers in the list. Pass a dictionary with integer keys, and obtain a superposition with amplitudes proportional to the values (the state is normalized for you).

```python
x = qq.reg([1,2,3,4])
qq.print(x)
# 1.0 w.p. 0.25
# 2.0 w.p. 0.25
# 3.0 w.p. 0.25
# 4.0 w.p. 0.25

x = qq.reg({0:3, 1:4})
qq.print(x)
# 0.0 w.p. 0.36  # = (3/4)^2
# 1.0 w.p. 0.64  # = (4/5)^2
```

Amplitudes can be displayed with `qq.print_amp`, similarly to `qq.print`. If not all registers are printed, then there may exist multiple branches that share a value. If this happens, multiple amplitudes are listed.

```python
x,y = qq.reg(10, range(3))

qq.print_amp(x) # 10.0 w.a. 0.57735, 0.57735, 0.57735

qq.print_amp(x,y)
# 10.0 0.0 w.a. 0.57735
# 10.0 1.0 w.a. 0.57735
# 10.0 2.0 w.a. 0.57735
```


### Cleaning up

When you are done with a quantum register `x`, you can get rid of it using `x.clean` and correctly guessing its current value.

```python
x = qq.reg([1,2])
x += 1
x.clean([2,3])
```

When you have a complicated quantum state and just want to get rid of it to avoid blowing up the number of branches, just use `qq.clear()`.

```python
# this will get super slow in later iterations
for i in range(1,10):
    x = qq.reg(range(5+i))
    # do something with x

# this is fast
for i in range(1,10):
    qq.clear()
    x = qq.reg(range(5+i))
    # do something with x
```

## Reversible programming

In classical programming we have many irreversible statements. Quantum computers are reversible, so Qumquat prohibits irreversible programming via some basic rules.

1. A statement cannot depend on the value of its target register. This prohibits `x ^= x` for example.
2. A controlling register cannot be the target of a statement.  See below for an example.

The basic operations `+=`, `-=`, `*=`, `//=`, `**=`, `^=`, `<<=` are usually reversible.

```python
x = qq.reg(3)

x *= 2    # now x is 6
# x *= 0  # raises IrrevError
x //= 2   # reversible since x is a multiple of 2. x is now 3.
# x //= 2  # raises IrrevError now that x is no longer a multiple of 2

x **= 2     # now x is 9
# x **= 0   # raises IrrevError
# x **= -1  # raises IrrevError (x would have to be a float, but must remain an integer)

x ^= 8   # now x is 1
x <<= 1  # now x is 2
```

#### If statements

Use `with qq.control(expr):` to perform statements only when `expr != 0`.

```python
x,y = qq.reg(range(3), 0)

with qq.control(x > 1): y += x 

qq.print(x,y)
# 0.0 0.0 w.p. 0.33333
# 1.0 0.0 w.p. 0.33333
# 2.0 2.0 w.p. 0.33333

# with qq.control(x > 1): x -= 1  # raises SyntaxError

# Z gate on index 1
if qq.control(x[1]): qq.phase_pi(1)
```

Quantum registers created inside a quantum if statement will always be allocated (to 0), but are only conditionally initialized.

```python
x = qq.reg([0,1])
with qq.control(x): y = qq.reg(2)
qq.print(y)
# 0.0 w.p. 0.5
# 2.0 w.p. 0.5
```

#### Inversion statements

To run a sequence of statements in reverse you can use `with qq.inv():`. 

```python
x = qq.reg([4,9,16])

with qq.inv():
    x += 3
    x **= 2

qq.print(x)
# -1.0 w.p. 0.33333
# 0.0 w.p. 0.33333
# 1.0 w.p. 0.33333
```

Inversion interacts interestingly with `qq.reg` - the inverse of of `x = qq.reg(42)` is `x.clean(42)`. But if you only write `qq.reg` without a matching `clean`, then inverted `qq.reg` will deallocate ... what register? You need to be really careful here.

```python
x = qq.reg(0)

with qq.inv():
    y = qq.reg(3) # uncompute register y
    x += y
    y.clean(3)    # create register y
    
qq.print(x)
# -3.0 w.p. 1.0

with qq.inv(): z = qq.reg(2)
# raises SyntaxError -> attempted to read register that was never allocated.
# z = qq.reg(2) is inverted to z.clean(2), but z is unallocated so there is nothing to clean.
```

## Expressions

Sometimes we need to evaluate a literal like `x+1` or access to floating point quantities `x/2`. When an arithmetic operation is performed on a quantum register, an expression object is created that holds onto a lambda expression. Consider for example:
```python

x = qq.reg(0)

expr = x+5

qq.print(expr)
# 5.0 w.p. 1.0

x += 1

qq.print(expr)
# 6.0 w.p. 1.0 
```

Observe how the value of the expression changes as `x` changes.

It is tempting to write the statement `x = x+1`, as in normal programming. But since `x+1` is an expression, `x` is now an expression not a register. This is a nasty bug becuase it is hard to spot.

```python
x = qq.reg(0)
print(x) # <Qumquat Key: 0, allocated>

# DON'T DO THIS! This will not behave as expected.
x = x+1
print(x) # <qumquat.qvars.Expression object at 0x7fae892bac88>

# Here are some functions that now fail:
x.qft(3) # raises AttributeError
x.had(0) # raises AttributeError
x.cnot(0,1) # raises AttributeError
x.assign(1) # raises AttributeError
x.clean(0) # raises AttributeError
```

Expressions are also immute to quantum control flow, like `qq.control` and `qq.inv`. Other than this particular pitfall, expressions should behave intuitively.

## Quantum Primitives

### Measurement

The function `qq.measure` samples a random value from the output distribution and collapses as little of the superposition as necessary.

```python
x = qq.reg([-1,1,-2,2])

out = qq.measure(x**2)
# outputs 1.0 or 4.0

qq.print(x)
# outputs either:
# -1.0 w.p. 0.5
# 1.0 w.p. 0.5
# or:
# -2.0 w.p. 0.5
# 2.0 w.p. 0.5
# so the sign stays in superposition!
```

Both `qq.measure` and `qq.print` utilize `qq.dist`. This is convenient for plotting.

```python
x,y = qq.reg(range(10), range(1,10))

values, probs = qq.dist(x % y)

# values[i] -> Measurement outcome: a float or a tuple of floats. Maybe strings.
# probs[i] -> Measurement probability.

import matplotlib.pyplot as plt
plt.bar(values, probs)

# or if you like one-liners
plt.bar(*qq.dist(x % y))

plt.show()
```

### Phase

The `qq.phase(theta)` method allows you to multiply the amplitude `e^(i*theta)`. To make this phase non-global `theta` should be an expression  or a register (or you are using a quantum if statement). For your convenience there are `qq.phase_pi(expr)` for `e^(i*pi*expr)` and `qq.phase_2pi(expr)` for `e^(2*pi*i*expr)`.

```python
x = qq.reg(range(3))

qq.phase(1) # this applies an unmeasurable global phase

from math import pi
# these all do the same thing
qq.phase(2*pi*x)
qq.phase_pi(2*x)
qq.phase_2pi(x)
```

### Quantum Fourier Transform

You can apply a QFT to a register `x` with `x.qft(d)`. Let `x = k*d + r`, where `r = x%d`. Then the QFT takes `|x>` to ` d^(-1/2)  sum_y e^(r * y * 2*pi*i/d) |k*d + y>`, where the sum is from `0` to `d-1`. It leaves the `k*d` part intact and only transforms `r`. 
```python
x = qq.reg(-4)
x.qft(4)
qq.print_amp(x)
# -4.0 w.a. 0.5
# -3.0 w.a. 0.5
# -2.0 w.a. 0.5
# -1.0 w.a. 0.5
qq.clear()

x = qq.reg(1)
x.qft(4)
qq.print_amp(x)
# 0.0 w.p. 0.5
# 1.0 w.p. 1j*0.5
# 2.0 w.p. -0.5
# 3.0 w.p. -1j*0.5
qq.clear()

x = qq.reg(6)
x.qft(4)
qq.print_amp(x)
# 4.0 w.p. 0.5
# 5.0 w.p. -0.5
# 6.0 w.p. 0.5
# 7.0 w.p. -0.5
```


### Low level bitwise operations

Qumquat registers are signed integers, not qubits. However in some situations, e.g. graph coloring, it might be more appropriate to view a register as an infinite sequence of qubits. A qumquat register `x` permits access to bits: `x[-1]` is the sign bit and `x[i]` is the `2^i` digit in the binary expansion. `x.len()` gives the minimum number of bits needed to write down the register.

```python
x = qq.reg(-10)
qq.print(*[x[i] for i in range(-1,4)])
# 1.0 0.0 1.0 0.0 1.0 w.p. 1.0
# sgn 2^0 2^1 2^2 2^3 
```

Hadamard and CNOT can be perfomed via `x.had(i)` and `x.cnot(ctrl, targ)`.  Qumquat is a high level language - you should not find the need to use Hadamard and CNOT unless you are doing nitty-gritty stuff. 

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

Qumquat actually implements a custom class `es_int` - explicitly signed int - for the registers. `es_int` behaves like a regular: python int, but `+0` and `-0` are different numbers, i.e `es_int(0) == -es_int(0)` evaluates to `False`. This is necessary because it should be possible to hadamard the sign bit regardless of the value of the rest of the register. However, this is just a technicality. The user should never have to care, especially since `qq.measure` casts to a float.

### QRAM

Given a dictionary whose keys are integers and values are either floats or integers, an expression can be used as a key to the dictionary via `expr.qram(dict)`.

```python
dic = {0:0.2, 1:0.4}
x = qq.reg([-1,1])
expr = (x+1)//2
qq.print(expr,expr.qram(dic))
# 0.0, 0.2 w.p. 0.5
# 1.0, 0.4 w.p. 0.5

# QRAM queries also work on lists
qq.print(expr,expr.qram([12.2, 42.1])
# 0.0, 12.2 w.p. 0.5
# 1.0, 42.1 w.p. 0.5
```

## State Preparation and Perp

The functions `qq.reg` and `x.clean` utilize a more versatile function `x.init` under the hood. Given a target state, specified by an expression, list or dictionary, `x.init` applies a unitary that maps `0` to the state. The remaining columns of the unitary are filled in an arbitrary but consistent manner.

```python
x = qq.reg(0)
x.init([0,1])
qq.print(x)
# 0.0 w.p. 0.5
# 1.0 w.p. 0.5
```

Since `x.init` behaves unpredictably on states other than the `0` state, it should be used with caution.

### Perp

A common situation where `x.init` is used is the flip a bit whenever a register is orthogonal to a target state.

```python
x = qq.reg(0)

with qq.inv(): x.init([0,1])
# if x was in the plus state, it is now in the 0 state.
p = qq.reg(x != 0)
x.init([0,1])

# now `p == 0` when `x` is in the plus state, `1` otherwise.
```

This trick is important, so to avoid bugs from misuse of `x.init`, this use case is encapsulated in `x.perp`. 

```python
x = qq.reg(0)
with x.perp([0,1]) as p:
    pass
    # now `p == 0` when `x` is in the plus state, `1` otherwise.
```

### Application: Measure state

A common application of `x.perp` is to measure in a basis containing a target state. For example, say we prepared `x` to be close to a target state and we want to test how close to the target we are. Then the probability returned by `qq.postselect` could be usedas follows:

```python
x = qq.reg(0)
target = [0,1]
# do something, e.g. amplitude amplification, to approximately turn x into target
with x.perp(target) as p:
    prob = qq.postselect(p == 0)
# x is now target, prob now contains magnitude square of overlap.
```
### Application: Grover's search

Another application of `x.perp` is amplitude amplification or Grover's search. While we usually do not have access to a unitary that prepares the target state (otherwise, why use amplitude amplifaction at all?) we need a utility to reflect around the initial state. 

```python
start = range(50) 
x = qq.reg(start)

# search for numbers that end in '7'
expr = (x % 10 == 7)

for i in range(5):
    # flip about target state
    qq.phase_pi(expr) 
    
    # flip abound initial state
    with x.perp(start) as p: qq.phase_pi(p)

# see how well we did
prob = qq.postselect(expr)
```

## Garbage Collection

Occasionally we would like to use irreversible statements like `x = 5`, which could be done on a quantum computer by copying the previous value to a hidden temporary register. Or, we might want to allocate new registers and clean them up automatically. As shown above `qq.inv` is not sufficient for these tasks: it can invert initialization but not allocation or cleaning.

The quantum garbage collector `@qq.garbage` is a decorator that lets you perform irreversible commands inside a subroutine. This function then can be used in a with statement.

As an example, this function efficiently computes `x^p mod N` using repeated squaring, an important step in Shor's algorithm. This function uses the irreversible `x.assign`, since I can't override python's assignment operator. This statement can violate rule (1.) above: `tmp.assign(tmp*tmp)` is allowed while `tmp *= tmp` is not.

```python
N = 23
p_bits = 3  # number of bits in p

@qq.garbage
def repeated_squaring(x, p):
    out = qq.reg(1)
    tmp = qq.reg(0)

    for i in range(p_bits):

        with qq.control(p[i]):
            # set tmp to x**(2**i)
            tmp.assign(x)
            for j in range(i): tmp.assign((tmp*tmp) % N)

            out *= tmp
            out %= N

    return out

x = 5
p = qq.reg([4,5,6,7])

with repeated_squaring(x, p) as out:
     qq.print("p =", p, "-> x**p mod N =", out)
# p = 4.0 -> x**p mod N = 4.0 w.p. 0.25
# p = 5.0 -> x**p mod N = 20.0 w.p. 0.25
# p = 6.0 -> x**p mod N = 8.0 w.p. 0.25
# p = 7.0 -> x**p mod N = 17.0 w.p. 0.25
```

The following irreversible statements utilize `x.assign` and are only available within a garbage-collected subroutine. These can also break rule 1.

```python
@qq.garbage
def irrev_demo(x):
    x.assign(x + 1)
    x[0] = 1 # set first bit
    x %= 10
    x >>= 1
    x &= x
    x |= x+1
    return x

x = qq.reg(range(4,8))
with irrev_demo(x) as out:
    y = qq.reg(out)

qq.print(x, y)
# 4.0 3.0 w.p. 0.25
# 5.0 7.0 w.p. 0.25
# 6.0 7.0 w.p. 0.25
# 7.0 5.0 w.p. 0.25
```

Normally reversible statements `+=`, `-=`, `*=`, `//=`, `**=`, `^=`, `<<=` still insist on reversiblity, so `x += x + 1` and `x *= qq.reg([0,1])` will still crash. If you want to protect against irreversiblity for these statements, just use `x.assign` like `x.assign(x + x + 1)` or `x.assign(x*qq.reg([0,1]))`.


## Snapshots

We often want to compare quantum states. Above we used `x.perp` to measure the inner product of a register and target state. If we want to measure the inner product between two pure states in two registers, we could use the swap test. The helper function `qq.swap` makes this trivial.  

```python
# registers to compare
x = qq.reg([0,1])
y = qq.reg(0)

# initialize test register to plus state
test = qq.reg([0,1])

# perform a controlled swap
with qq.control(test): qq.swap(x,y)

# measure the plus state
with test.perp([0,1]) as p:
    prob = qq.postselect(p == 0) # = 0.5*(1 + |<x|y>|^2)
print(qq.sqrt(2*prob - 1)) # magnitude of inner product
```

However, if we are comparing mixed states we are interested in fidelity and trace distance. For more definitions see section 1.2.4 of [Scott Aaronson's Barbados notes](https://www.scottaaronson.com/barbados-2016.pdf). Quantum algorithms for computing these are tricky (see [arXiv:1310.2035](https://arxiv.org/abs/1310.2035)).

The snapshot feature `qq.snap` permits easy access to fidelity and trace distance. While the qumquat simulation only permits pure states, a snapshot can temporarily store a mixed state for comparison purposes.

```python
x = qq.reg([0,1]) # plus state
snap1 = qq.snap(x)

tmp = qq.reg(x) # x is now maximally mixed state
# since it is entangled with tmp

snap2 = qq.snap(x)

print("Fidelity:", qq.fidelity(snap1,snap2))
print("Trace distance:", qq.trace_dist(snap1,snap2))

qq.clear()
# qq.snap also supports expressions and multiple expressions

x = qq.reg([0,1])
y = qq.reg([2,3])

snap1 = qq.snap(x+1, y)
snap2 = qq.snap(y-1, x)
print("Fidelity:", qq.fidelity(snap1,snap2))
print("Trace distance:", qq.trace_dist(snap1,snap2))
```

