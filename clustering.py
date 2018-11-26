import qumquat as qq
import random, math

# quant-ph/1307.0411
# estimate distance of vector u from centroid of {v_i}

N = 20 # dimension
M = 10 # number of vectors in cluster

u = [random.uniform(-5, 5) for i in range(N)]
u_norm = math.sqrt(sum([x**2 for x in u]))

vs = []
for j in range(M):
    vs.append([random.uniform(-1,1) for i in range(N)])

v_norms = [math.sqrt(sum([x**2 for x in vs[j]])) for j in range(M)]


####### classical calculation
delta = [u[i] for i in range(N)]
for j in range(M):
    for i in range(N):
        delta[i] += vs[j][i]/M

distance = math.sqrt(sum([x**2 for x in delta]))


######################## quantum algorithm

# TODO: compute this using quantum counting.
# This classical method takes linear time.
Z = u_norm**2 + sum([v_norm**2 for v_norm in v_norms])/M

############## prepare state phi in phi_key

tmp = qq.reg([0,1])
with qq.q_if(tmp): phi_key = qq.reg(range(1,M+1))
tmp.clean(phi_key > 0)

# calculate t for hamiltonian
t = 1e-8 * min(1/u_norm, min([1/v_norm for v_norm in v_norms]))
print("t =", t)
print("sin(|u|*t) - |u|*t is", math.sin(u_norm*t) - u_norm*t, "\n")

# ancilla in |+> state (on sign bit)
tmp = qq.reg([-1,1])

# apply hamiltonian (with sigma_Z instead of sigma_X) - that way it's diagonal
with qq.q_if(phi_key == 0): qq.phase(t*u_norm * tmp)
with qq.q_if(phi_key > 0): qq.phase(t*(phi_key-1).qram(v_norms) * tmp)

# postselect the ancilla
tmp.had(-1)

phi_prob = qq.postselect(tmp < 0)
print("prepared phi with probability", phi_prob)
print("Z**2 * t**2 =", Z**2 * t**2, "\n")

############## prepare state psi in psi_key and psi_value

# prepare ( |0> + M^(-1/2) sum_{j=1}^M |j> ) * 2^{-1/2}
tmp = qq.reg([0,1])
with qq.q_if(tmp): psi_key = qq.reg(range(1,M+1))
tmp.clean(psi_key > 0)

# prepare state into this register
psi_value = qq.reg(0)

with qq.q_if(psi_key == 0):
    qq.init(psi_value, {i:u[i] for i in range(N)})

# even qumquat can't query different QRAMs in superposition in constant time
for j in range(M):
    with qq.q_if(psi_key-1 == j):
        qq.init(psi_value, {i:vs[j][i] for i in range(N)})


############# estimate distance
# states phi and psi are now prepared.
# perform swap test phi_key and psi_key

out = qq.reg([0,1])
with qq.q_if(out):
    qq.utils.swap(phi_key, psi_key)
out.had(0)

p_success = qq.postselect(out == 0)

print("quantum probability:", p_success)
print("quantum distance:", math.sqrt(Z*p_success))
print("classical distance:", distance)
