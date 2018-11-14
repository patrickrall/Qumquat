import qumquat as qq
from qvars import es_int
import matplotlib.pyplot as plt
import math


def test_init():
    print("init")

    # ints and es_ints
    x = qq.reg(1)
    x.clean(es_int(1))

    x = qq.reg(1)
    x.clean(1)

    # superpositions
    x = qq.reg([1,es_int(2),3])
    x.clean([1,2,es_int(3)])

    # other variables
    x = qq.reg(range(5))
    y = qq.reg(x)
    z = qq.reg(x // 2)
    qq.print(x,y,z)
    z.clean(y // 2)
    x.clean(y)
    y.clean(range(5))


def test_inv():
    print("inv")
    x,y = qq.reg(0,1)

    def stuff(x):
        x += 1
        x -= (y+5)//2
        x *= y
        # x *= 0 causes IrrevError
        x -= 2
        x //= 1
        # x //= 2 causes IrrevError
        x ^= (y+1)

    stuff(x)
    qq.print(x)
    with qq.inv(): stuff(x)

    x.clean(0)
    y.clean(1)

def test_if():
    print("if")
    x = qq.reg([0,1])
    y = qq.reg(0)

    with qq.q_if(x): y += 1
    qq.print(x, y)
    with qq.q_if(x == 0): y += 1

    y.clean(1)
    x.clean([0,1])


def test_quantum():
    print("quantum")
    #### simple quantum teleportation test

    y = qq.reg([-1, 1])
    with qq.q_if(y < 0): qq.phase_pi(1) # Z gate
    # y[-1] now |->

    # Bell state
    x = qq.reg(0)
    x.had(0)
    x.cnot(0,1)

    # cnot across registers
    with qq.q_if(y[-1]): x ^= 1

    # measure
    x_meas = int(qq.measure(x[0]))
    y.had(-1)
    y_meas = int(qq.measure(y[-1]))

    # apply x correction and z correction
    if x_meas: x ^= 2
    with qq.q_if(y_meas & x[1]): qq.phase_pi(1)

    # x[1] is now |->
    x.had(1)
    x.clean(x_meas + 2)

    #### gentle measurement test
    x = qq.reg([-5,5,-2,2])
    out = qq.measure(x**2)
    qq.print(x)


def test_inv_if():
    print("inv if")
    x, y = qq.reg([0,1], 0)

    with qq.inv():
        with qq.q_if(x):
            y += 1

    with qq.q_if(y):
        with qq.inv():
            x += 1

    qq.print(x,y)
    x.clean(0)
    y.clean([0,-1])


def test_while():
    print("while")

    x, y, l = qq.reg(1, [10,15,16], 0)

    with qq.q_while(x < y, l): x += 2
    qq.print(x,y,l)

    with qq.inv():
        with qq.q_while(x < y, l): x += 2

    x.clean(1)
    y.clean([10,15,16])
    l.clean(0)


def test_collatz():
    print("collatz")
    # collatz test

    x, l = qq.reg(range(1,11), 0)
    y = qq.reg(x)

    # nested while
    with qq.q_while(x > 1, l):

        tmp = qq.reg(x % 2)

        with qq.q_if(tmp == 0):
            x //= 2

        with qq.q_if(tmp == 1):
            x *= 3
            x += 1

    qq.print(y,l)

def test_order():
    print("order")
    n = 5
    x = qq.reg(range(2**n))

    qq.reg((7**x).int() % 15) # has period 4

    with qq.inv(): x.qft(2**n)

    vals, probs, _ = qq.distribution(x)
    plt.plot(vals,probs)
    plt.show()

def test_garbage_1():
    print("garbage 1")

    with qq.garbage():
        x = qq.reg(1)
        y = qq.reg(2)
        x += 1

        with qq.inv():
            xp = qq.reg(1)
            yp = qq.reg(2)
            xp += 1

def test_garbage_2():
    print("garbage 2")

    @qq.garbage("test")
    def messy(x):
        out = qq.reg(x)

        for i in [100, 200, 300]:
            with qq.q_while(x*out < i, qq.reg(0)):
                out += 1

        return out

    x = qq.reg([2,4,7,8])

    out = qq.reg(messy(x))

    with qq.inv(): messy(x)

    qq.print(x,out,x*out)


def test_garbage_3():
    print("garbage 3")
    a = qq.reg(1)

    with qq.garbage("test"):
        x = qq.reg(1)
        x += a

    with qq.garbage("test"):
        y = qq.reg(2)
        z = qq.reg(3)
        y += 3

    with qq.garbage("test-2"):
        y = qq.reg(8)
        y += 2

    with qq.garbage("test"):
        with qq.inv(): qq.reg(2)
        z.clean(3)

    with qq.garbage("test"):
        with qq.inv(): qq.reg(5)

    with qq.garbage("test-2"):
        with qq.inv(): qq.reg(10)


def test_garbage_4():
    print("garbage 4")
    x = qq.reg(5)

    with qq.garbage():
        x.assign(3)
        qq.print("assign(3) yields", x)
        with qq.inv(): x.assign(3)


    with qq.garbage():
        qq.print("before bitset",*[x[i] for i in range(-1,3)])
        x[-1] = 1
        x[1] = 1
        qq.print("bitset yields",*[x[i] for i in range(-1,3)])
        with qq.inv():
            x[-1] = 1
            x[1] = 1


def test_garbage_5():
    print("garbage 5")
    i = qq.reg(0)
    tmp = qq.reg(0)
    with qq.garbage():

        with qq.q_while(i < 4, tmp):
            x = qq.reg(i)
            i += 1

        with qq.inv():
            with qq.q_while(i < 4, tmp):
                x = qq.reg(i)
                i += 1

    i.clean(0)
    tmp.clean(0)

# grover's search on max clique
def grover():
    print("grover")
    n = 8

    # generate a random graph
    import random
    k = 4
    edges = []
    for i in range(n):
        for j in range(i+1,n):
            if i != j+1 % n:
                edges.append([i,j])
            # if random.random() > 0.5:


    @qq.garbage("oracle")
    def oracle(x):
        num_bad = qq.reg(0)
        clique_size = qq.reg(0)

        for i in range(n):
            with qq.q_if(x[i]): clique_size += 1

            for j in range(i+1,n):
                if [i,j] not in edges:
                    with qq.q_if(x[i] & x[j]): num_bad += 1

        return (num_bad == 0) & (clique_size >= k)

    x = qq.reg(range(2**n))


    for i in range(1):
        with qq.q_if(oracle(x)): qq.phase_pi(1)
        with qq.inv(): oracle(x)

        for j in range(n): x.had(j)
        with qq.q_if(x == 0): qq.phase_pi(1)
        for j in range(n): x.had(j)


    values, probs, _ = qq.distribution(x)
    plt.bar(values, probs)
    plt.show()

def test_repeated_square():
    print("repeated square")

    @qq.garbage("repsquare")
    def rep_square(b, x, N):
        out = qq.reg(0)
        tmp = qq.reg(b)
        for i in range(5):
            with qq.q_if(x[i]): out += tmp
            tmp **= 2
            tmp %= N
        return out % 13

    x = qq.reg(range(16))
    out = qq.reg(0)
    with qq.garbage():
        out += rep_square(7, x, 13)
        with qq.inv(): rep_square(7, x, 13)
        qq.assert_pile_clean('repsquare')

    qq.print(x,out, 7**x % 13)

def test_for():
    print("for")
    class q_for():
        def __init__(self, i, maxval):
            self.i = i
            self.maxval = maxval
            self.tmp = qq.reg(0) # temporary register

            # compute the number of iterations
            self.num_iter = qq.reg(0)
            with qq.q_if(i < maxval):
                self.num_iter += maxval - i

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
    i.clean(3)


    qq.print(x,out)

def test_qft():
    print("qft")
    for i in range(-10,10,3):
        qq.clear()

        print(i)
        x = qq.reg(i)
        x.qft(4)
        qq.print(x)


if True:
    test_init()
    test_inv()
    test_if()
    test_quantum()
    test_inv_if()
    test_while()
    test_collatz()
    # test_order() # has plot
    test_garbage_1()
    test_garbage_2()
    test_garbage_3()
    test_garbage_4()
    test_garbage_5()
    # grover() # has plot
    test_repeated_square()
    test_for()
    test_qft()

