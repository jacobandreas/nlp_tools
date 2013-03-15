import math_utils as mu
import dict_utils as du

class Semiring:

  def __init__(self, zero, one, sum_op, prod_op):
    self.zero = zero
    self.one = one
    self.sum_op = sum_op
    self.prod_op = prod_op

class DebugSemiring(Semiring):

  def __init__(self):
    pass

  def zero(self):
    return None

  def one(self):
    return ''

  def sum_op(self, values):
    return ' OR '.join(['(%s)' % val for val in values])

  def prod_op(self, values):
    return ' AND '.join(['(%s)' % val for val in values if val != ''])

class LogLinearExpectationSemiring(Semiring):

  def __init__(self):
    pass

  def zero(self):
    return (-float('Inf'), {})

  def one(self):
    return (0, {})

  def sum_op(self, values):
    probs = [pr for pr,ex in values]
    exps = [ex for pr,ex in values]
    return (mu.logspace_sum(probs),
            du.d_logspace_sum(exps))

  def prod_op(self, values):
    exps = [ex for pr,ex in values]
    for i in range(len(values)):
      pr,ex = values[i]
      for j in range(len(exps)):
        if i == j:
          continue
        exps[j] = du.d_logspace_scalar_prod(pr, exps[j])

    return (mu.logspace_prod([pr for pr,ex in values]),
            du.d_logspace_sum(exps))
