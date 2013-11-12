"""
Useful math functions that don't come baked in with python.
"""

import math
import sys

def logspace_sum(args):
  """
  Computes the sum of input args represented in logspace.
  That is, computes log(sum(exp(a) for a in args)), but with adjustments for
  numerical stability.
  """
  biggest = max(args)
  bindex = args.index(biggest)
  exp_part = sum(math.exp(args[i] - biggest) for i in range(len(args)) if i !=
      bindex)
  if 0 < exp_part < 1:
    return biggest + math.log1p(exp_part)
  return biggest + math.log(1 + exp_part)

def logspace_prod(args):
  """
  Self-documenting logspace product (i.e. just a sum).
  """
  return sum(args)


def checkgrad(fn, eps=0.001):
  def checked_fn(x, *args):
    l, jac = fn(x, *args)

    assert x.shape == jac.shape
    assert len(x.shape) == 1

    for i in range(x.shape[0]):
      lpred = jac[i] * eps
      xdisp = x.copy()
      xdisp[i] += eps
      ltrue = fn(xdisp, *args)[0] - l
      print 'd: %f\tp: %f\tt: %f' % (lpred - ltrue, lpred, ltrue)
    sys.stdin.readline()

    return l, jac

  return checked_fn
