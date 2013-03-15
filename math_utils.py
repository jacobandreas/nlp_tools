"""
Useful math functions that don't come baked in with python.
"""

import math

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
