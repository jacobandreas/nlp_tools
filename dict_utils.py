import math_utils as mu
import math

def d_sum(*args):
  """
  Adds the dictionaries together elementwise. Missing entries are assumed to be
  zero.
  """
  ret = {}
  for d in args:
    for key in d:
      if key not in ret:
        ret[key] = d[key]
      else:
        ret[key] += d[key]
  for key in ret.keys():
    if ret[key] == 0:
      del ret[key]
  return ret

def d_elt_prod(*args):
  """
  Multiplies the dictionaries together elementwise. Missing entries are assumed
  to be zero.
  """
  # avoid querying lots of nonexistent keys
  smallest = min(args, key=len)
  sindex = args.index(smallest)
  ret = dict(smallest)
  for i in range(len(args)):
    if i == sindex:
      continue
    d = args[i]
    for key in ret.keys():
      if key in d:
        ret[key] *= d[key]
      else:
        del ret[key]
  return ret

def d_dot_prod(d1, d2):
  """
  Takes the dot product of the two dictionaries.
  """
  # avoid querying lots of nonexistent keys
  if len(d2) < len(d1):
    d1, d2 = d2, d1
  dot_prod = 0
  for key in d1:
    if key in d2:
      dot_prod += d1[key] * d2[key]
  return dot_prod

def d_op(op, d):
  """
  Applies op to every element of the dictionary.
  """
  ret = {}
  for key in d:
    ret[key] = op(d[key])
  return ret

# convenience methods
def d_log(d):
  return d_op(math.log, d)

def d_exp(d):
  return d_op(math.exp, d)
