import qumquat as qq
import math

lambdas = [0.1, 0.3, 0.5, 0.7, 0.9] # phases. all odd so intervals of 0.2 are 'good'
T = 33 # dimension of estimation register

print("T =",T)

def phase_est(E,I):
    qq.phase(E*I.qram(lambdas)*2*math.pi)
    with qq.inv(): E.qft(T)

if False:
    print("phase estimation")
    I = qq.reg(1)

    E = qq.reg(range(T))

    phase_est(E,I)
    estimate = qq.reg(E)/T
    with qq.inv(): phase_est(E,I)

    delta = 0.05
    error = ((estimate - lambdas[1]) % 1)
    eps = 1 - qq.postselect((error < delta) | (error > 1-delta))
    print("eps:", round(eps,5), "delta:", delta)


if False:
    print("Thresholding")

    I = qq.reg(range(5))

    qq.phase_2pi(I/5)

    print("I before:")
    qq.print_amp(I)

    E = qq.reg(range(T))
    phase_est(E,I)

    prob = qq.postselect(E/T > 0.6)
    print("postselection success:", prob)

    with qq.inv(): phase_est(E,I)

    print("\nI after thresholding:")
    qq.print(I)

    E.qft(T)
    print("\nE is 0 w.p.", qq.postselect(E == 0))


    print("\nI after postselecting E:")
    qq.print_amp(I)

    print("\ntarget state:")
    qq.clear()
    y = qq.reg([3,4])
    qq.phase_2pi(y/5)
    qq.print_amp(y)

if True:
    print("consistent phase estimation")
    # http://www.cs.tau.ac.il/~amnon/Papers/T.stoc13.IntQLog.pdf

    I = qq.reg(1)
    E = qq.reg(range(T))

    phase_est(E,I)

    lambdatilde = qq.reg((E*10/T).floor())/10

    with qq.inv(): phase_est(E,I)

    qq.print(lambdatilde)


