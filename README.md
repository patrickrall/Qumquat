# Qumquat
## Quantum Machine Learning and Quantum Algorithms Toolkit

Qumquat is an experimental high-level quantum programming language. This language is aimed to provide a comfortable environment for experimenting with algorithms like HHL, quantum semidefinite programming, quantum counting, quantum reccomendation systems and quantum convex optimization.  Guiding ideas:

 - These algorithms demand **reversible classical computation in superposition**. Qumquat is designed to feel like any other imperative programming language to make classical programming comfortable.
 - These algorithms do not run on NISQ quantum computers, so **Qumquat never 'compiles' to quantum gates** or even explicitly stores qubits. Since the runtime will always be a classical simulation, infinite-dimensional quantum registers and quantum while loops are possible.
 - Simply implementing an algorithm is an excellent way of solidifying one's understanding and also **ensure that the algorithm behaves as expected**. Qumquat is intended as an **educational tool for all levels of experience** in quantum computation.

Qumquat is a side project that took 1.5 weeks to speed-code. So the documentation and code quality is abysmal, but the basic functionality works.

### Quantum Registers

Quantum registers are created with `qq.reg`. **Qumquat registers are always signed integers**.

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
z = qq.reg([1,1]) # will raise ValueError

# You can also copy another register
w = qq.reg(y)
```

When you are done with a register you should clean it up, because garbage can mess up the interference pattern your quantum algorithm is creating. To clean up a register, simply guess its value and call `x.clean`.

```python
x,y = qq.reg(10, range(3))
x += 3

x.clean(13) # register x is now deallocated
x += 1 # raises SyntaxError

z = qq.reg(y)

# y.clean(range(3)) # will fail to uncompute since y is entangled with z
y.clean(z)

z.clean(range(3)) 
```

Operations `+=`, `-=`, `*=`, `//=`, `**=`, `^=`, `<<=` are permitted whenever they are reversible. Irreversible operations exist as well, but they require the garbage collector.

```python

x = qq.reg(3)

x *= 2    # now x is 6
x *= 0  # raises IrrevError
x //= 2   # reversible since x is a multiple of 2. x is now 3.
x //= 2  # raises IrrevError now that x is no longer a multiple of 2

x **= 2     # now x is 9
x **= 0   # raises IrrevError
x **= -1  # raises IrrevError (x would have to be a float)

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
# This bug is nasty since it can be hard to spot - operations like +=
# are still defined on expressions. Here are some functions that now fail:
x.qft(3) # raises AttributeError
x.had(0) # raises AttributeError
x.cnot(0,1) # raises AttributeError
x.assign(1) # raises AttributeError
x.clean(0) # raises AttributeError

```
If a successor of this language were to compile to a real quantum computer, it would allocate extra qubits to temporarily hold on to the value of the expression. These qubits would then be immediately uncomputed automatically.

#### Measurement

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

#### Quantum Fourier Transform

You can apply a QFT to a register `x` with `x.qft(d)`. Let `x = k*d + r`, where `r = x%d`. Then the QFT takes `|x>` to ` d^(-1/2)  sum_y e^(r * y * 2*pi*i/d) |k*d + y>`, where the sum is from `0` to `d-1`. It leaves the `k*d` part intact and only transforms `r`. 
```python
x,y,z = qq.reg(-2, 1, 6)

x.qft(4)
y.qft(4)
z.qft(4)

qq.print(x)
-4.0 w.p. 0.25
-3.0 w.p. 0.25
-2.0 w.p. 0.25
-1.0 w.p. 0.25

qq.print(y)
0.0 w.p. 0.25
1.0 w.p. 0.25
2.0 w.p. 0.25
3.0 w.p. 0.25

qq.print(z)
4.0 w.p. 0.25
5.0 w.p. 0.25
6.0 w.p. 0.25
7.0 w.p. 0.25
```

#### Clear

If your are done with all of the registers and don't want to go through the trouble of cleaning them up, you can clear the state of Qumquat with `qq.clear()`. This strongly improves performance.

```python
# this gets super slow for later operations
# as the number of branches increases exponentially
for i in range(3,10):
    x = qq.reg(i)
    x.qft(5)
    qq.print(x)

# this is fast
for i in range(3,10):
    qq.clear()
    x = qq.reg(i)
    x.qft(5)
    qq.print(x)
```


#### Low level bitwise operations

Qumquat registers are signed integers, not qubits. However in some situations, e.g. graph coloring, it might be more appropriate to view a register as an infinite sequence of qubits. A qumquat register `x` permit access to bits: `x[-1]` is the sign bit and `x[i]` is the `2^i` digit in the binary expansion. `x.len()` gives the minumum number of bits needed to write down the register.

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

Qumquat actually implements a custom class `es_int` - explicitly signed int - for the registers. `es_int` quacks like a regular python int, but `+0` and `-0` are different numbers, i.e `es_int(0) == -es_int(0)` evaluates to `False`. This is necessary because it should be possible to hadamard the sign bit regardless of the value of the rest of the register. However, this is just a technicality. The user should never have to care, especially since `qq.measure` casts to a float.


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

with qq.q_if(x > 1): x -= 1  # raises SyntaxError

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

# add 3 modulo 8
n = 3

x_prv = qq.reg([1,5,7])
x = qq.reg(x_prv)
x.qft(2**n)
omega(3*x, n)
with qq.inv(): x.qft(2**n)

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

with qq.inv(): z = qq.reg(2)
# raises SyntaxError -> attempted to read register that was never allocated.
z = qq.reg(2) is inverted to z.clean(2), but z is unallocated.
```

So how does one uncompute garbage? This situation is unsatisfying because it encourages you to factor out your garbage registers as shown below. The quantum garbage collector makes this easier.

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
x, y = qq.reg([2,3,4,5], 0)
i, tmp = qq.reg(0,0)

# goal:
# for i in range(x): y += i**2

with qq.q_while(i < x, tmp):
    y += i**2
    i += 1

# since x = i = tmp we can uncompute i and tmp
i.clean(x)
tmp.clean(x)

qq.print(x,y,i,tmp)
# 2.0 1.0 w.p. 0.25
# 3.0 5.0 w.p. 0.25
# 4.0 14.0 w.p. 0.25
# 5.0 30.0 w.p. 0.25
```

Since for loops are just while loops in disguise, let's implement a for loop. Python's `with` statement calls the `__enter__` and `__exit__` methods before and after the code block respectively. Since it is possible to predict the number of loops from the initial conditions we can immediately uncompute the temporary register and return the loop variable to its initial value.

```python
class q_for():
    def __init__(self, i, maxval):
        self.i = i
        self.maxval = maxval

        # compute the number of iterations
        self.num_iter = qq.reg(0)
        with qq.q_if(i < maxval):
            self.num_iter += maxval - i

        self.tmp = qq.reg(0) # temporary register
        self.q_while = qq.q_while(i < maxval, self.tmp)

    def __enter__(self):
        self.q_while.__enter__()

    def __exit__(self, *args):
        self.i += 1
        self.q_while.__exit__()

        # clean the temporary register
        self.tmp.clean(self.num_iter)

        # return i to previous value
        self.i -= self.num_iter

        # uncompute the number of iterations
        with qq.q_if(self.i < self.maxval):
            self.num_iter -= self.maxval - self.i
        self.num_iter.clean(0)


x = qq.reg([2,3,4,5])
out = qq.reg(0)

i = qq.reg(3)
with q_for(i, x):
    out += i**2
i.clean(3) # i is returned to initial value

qq.print(x,out)
# 2.0 0.0 w.p. 0.25
# 3.0 0.0 w.p. 0.25
# 4.0 9.0 w.p. 0.25
# 5.0 25.0 w.p. 0.25
```

Is returning the loop variable to its initial value always the best choice? What if you want to loop in reverse order, or change the step size? Implementing a more general for loop would be complicated and it would be confusing to use. This is why Qumquat just implements the while loop - the user can decide what makes sense from context.


### Quantum Garbage Collection

Reversible computation is a bit annoying - you have to follow annoying rules to ensure reversiblity, and whenever you use temporary registers you have to worry about cleaning them up. This can be tricky as the for loop example shows. 

Ideally, you should be able to declare as many temporary registers as you want without worry and write irreversible code, and have uncomputing still work. The quantum garbage collector mostly enables this.

As shown above `qq.inv()` on its own is not smart enough to uncompute allocations. The following code will not behave as expected:
```python
x = qq.reg(2)
with qq.inv(): x = qq.reg(2)  # this does not uncompute the previous line
```
In fact the above code crashes. But with `qq.garbage()` it works:
```python
with qq.garbage():
    x = qq.reg(2)
    with qq.inv(): x = qq.reg(2)  # uncomputes the previous line
```

#### How it works

`qq.reg` is a bit subtle. Consider the following piece of code:
```python
i = qq.reg(0)
with qq.q_while(i < 3, qq.reg(0)):
    x = qq.reg(i)
    i += 1
```
The while loop executes three times, but python only executes the contents of a `with` environment once, so `qq.reg` is actually only once. Despite this, three registers are allocated, so `x` refers to multiple registers!

This illustrates that `qq.reg` does not actually return a register. It returns a `Key` - a more complicated object that maintains references to registers. Sometimes keys can refer to multiple registers as above.

In order to perform garbage collection we also need the opposite: multiple keys refer to the same register. Even though the uncompute operation creates new `Key` objects, they refer to registers that were allocated previously. When garbage collection is turned on, `Key` objects will automatically organize themselves into pairs.

```python
with qq.garbage():
    x = qq.reg(1) # key 0
    y = qq.reg(2) # key 1
    with qq.inv(): 
        qq.reg(1) # key 2, paired to key 1
        qq.reg(2) # key 4, paired to key 1
````

The ordering of the keys determines the pair matching, so be careful. The following code might make sense, but the `Key` are not smart enough to pair themselves correctly.

```python
with qq.garbage():
    x = qq.reg(1) # key 0
    y = qq.reg(2) # key 1
    with qq.inv(): qq.reg(2) # key 2, paired to 1. Uncompute fails -> crash
    with qq.inv(): qq.reg(1)
````

If a key refers to multiple registers, as it did in the first example, the partner key must also refer to multiple registers.

```python
i = qq.reg(0)    # key 0, not garbage collected
tmp = qq.reg(0)  # key 1, not garbage collected

with qq.garbage():

    with qq.q_while(i < 3, tmp):
        x = qq.reg(i) # key 2, allocated 3 times
        i += 1

    with qq.inv():
        with qq.q_while(i < 3, tmp):
            x = qq.reg(i) # key 3, paired to key 2, deallocated 3 times
            i += 1
            
i.clean(0)
tmp.clean(0)
```

#### Garbage piles

`qq.garbage` can be used in multiple ways. If you call `qq.garbage()` then the collector insists that everything is cleaned up within the same scope.

```python
with qq.garbage():
    x = qq.reg(2)
    # crashes at end of scope! Not all keys were cleaned up!
    
with qq.garbage():
    with qq.inv(): x = qq.reg(2)
```

But you can also put your keys into a 'garbage pile' and clean them up later. Do this with `qq.garbage('pile name')`:

```python
with qq.garbage('demo'):
    x = qq.reg(2)  # key 0

# garbage pile 'demo' now contains key 0
    
with qq.garbage('demo'):
    with qq.inv(): x = qq.reg(2) # key 1, matched to key 0
    
# If you really want to be careful with your garbage:
qq.assert_pile_clean('demo')
```

This is especially useful for calling subroutines. so you can use `qq.garbage` as a decorator. For example:

```python
@qq.garbage('subroutine')
def messy_function(x):
    i, out = qq.reg(0,2)
    with qq.q_while(i < x, qq.reg(0)):
        tmp = qq.reg(i % out)
        out += tmp
        i += 1

    return out

input = qq.reg([1,2,3,4,5])
output = qq.reg(messy_function(input))
with qq.inv(): messy_function(input)

qq.print(input, output)

qq.assert_pile_clean('subroutine')
# 1.0 2.0 w.p. 0.2
# 2.0 3.0 w.p. 0.2
# 3.0 5.0 w.p. 0.2
# 4.0 8.0 w.p. 0.2
# 5.0 12.0 w.p. 0.2

qq.assert_pile_clean('subroutine')
```

The above subroutine allocates variables left and right without a care in the world, and it is all cleaned up automatically.

#### Irreversible operations

Now that making temporary variables is no longer cumbersome, we can use irreversible statements like `x.assign`. We can also break rule 1: the statements can now depend to their target, e.g. `x.assign(x+1)`.
```python
@qq.garbage('irrev_demo')
def irrev_demo(x):
    x.assign(x + 1)
    x[0] = 1 # set first bit
    x %= 10
    x >>= 1
    x &= x
    x |= x+1
    return x

input = qq.reg(range(4,8))
output = qq.reg(irrev_demo(input))
with qq.inv(): irrev_demo(input)

qq.print(input, output)
# 4.0 3.0 w.p. 0.25
# 5.0 7.0 w.p. 0.25
# 6.0 7.0 w.p. 0.25
# 7.0 5.0 w.p. 0.25
```

Normally reversible statements `+=`, `-=`, `*=`, `//=`, `**=`, `^=`, `<<=` still insist on reversiblity, so `x += x + 1` and `x *= qq.reg([0,1])` will still crash. If you want to protect against irreversiblity for these statements, just use `x.assign` like `x.assign(x + x + 1)` or `x.assign(x*qq.reg([0,1]))`.
