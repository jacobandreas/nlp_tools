import numpy as np
import math

def adagrad(f, x0, eta, delta):
  dim = x0.shape[0]
  x = np.zeros((dim, 1))
  g_iters = np.zeros((dim, 0))

  last_fval = f(x)[0]

  for t in range(500):
    fval, fjac = f(x)
    fjac = fjac.reshape((dim,1))

    g_iters = np.hstack((g_iters, fjac))
    s = np.zeros((dim,))
    for i in range(dim):
      s[i] = g_iters[i,:].dot(g_iters[i,:])
    #print np.diag(s)
    h = delta * np.eye(dim) + np.diag(s)
    #print h 
    gsum = np.sum(g_iters, 1)
    #print gsum
    x = np.linalg.solve(h, -(gsum))
    last_fval = fval

  return x
