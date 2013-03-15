import math

def logspace_add(*args):
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
