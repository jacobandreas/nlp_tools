from nlp_tools.list_utils import flatten

class LambdaExpr:

  LAMBDA = 'lambda'
  UNICODE_LAMBDA = u'\u03bb';
  ALTERNATE_LAMBDAS = ('\\', 'lambda')
  SPECIALS = ('argmin', 'argmax', 'exists', 'count', 'the')

  def __init__(self, sexp):
    self.sexp = sexp
    if isinstance(sexp, list):
      toks = list(flatten(sexp))
    else:
      toks = [sexp]
    varz = [int(t[1:]) for t in toks if t[0] == '$']
    if varz:
      self.next_var = max(varz) + 1
    else:
      self.next_var = 0

  @classmethod
  def from_string(cls, string):
    if '(' not in string:
      return LambdaExpr(string)
    string = string.replace('(', '( ')
    string = string.replace(')', ' )')
    toks = string.split()
    toks.reverse()
    list_stack = []
    this_list = None
    while toks:
      tok = toks.pop()
      if tok == '(':
        this_list = []
        list_stack.append(this_list)
      elif tok == ')':
        last_list = list_stack.pop()
        if not list_stack:
          assert not toks
          return LambdaExpr(last_list)
        else:
          this_list = list_stack[-1]
          this_list.append(last_list)
      else:
        if tok in cls.ALTERNATE_LAMBDAS:
          tok = cls.LAMBDA
        this_list.append(tok)

  def __str__(self):
    return self.__str_inner(self.sexp)

  def __repr__(self):
    return str(self)

  def __ustr__(self):
    return self.__str__().replace(self.LAMBDA, self.UNICODE_LAMBDA)

  def __str_inner(self, sexp):
    if isinstance(sexp, list):
      return '(%s)' % ' '.join([self.__str_inner(tok) for tok in sexp])
    return sexp

  def is_lambda(self):
    return isinstance(self.sexp, list) and self.sexp[0] == self.LAMBDA

  def is_atom(self):
    return not isinstance(self.sexp, list)

  def bound_vars(self):
    return self.__bound_vars_inner(self.sexp)

  def __bound_vars_inner(self, sexp):
    if not isinstance(sexp, list):
      return set()
    if sexp[0] == self.LAMBDA:
      return set([sexp[1]]) | self.__bound_vars_inner(sexp[3])
    elif sexp[0] in self.SPECIALS:
      r = set([sexp[1]])
      for t in sexp[2:]:
        r |= self.__bound_vars_inner(t)
      return r
    else:
      r = set()
      for t in sexp[1:]:
        r |= self.__bound_vars_inner(t)
      return r

  def renumber_from(self, start):
    bound = self.bound_vars()
    return LambdaExpr(self.__renumber_from_inner(start, bound, self.sexp))

  def __renumber_from_inner(self, start, bound, sexp):
    if isinstance(sexp, list):
      return [self.__renumber_from_inner(start, bound, s) for s in sexp]
    #if sexp[0] == '$':
    if sexp in bound:
      return '$%d' % (int(sexp[1:]) + start)
    else:
      return sexp
    
  def compose(self, arg):
    assert isinstance(arg, LambdaExpr)
    #assert not self.is_atom() and self.sexp[0] == self.LAMBDA
    assert not self.is_atom()
    assert self.sexp[0] == self.LAMBDA
    return LambdaExpr([
      self.LAMBDA,
      self.sexp[1],
      # TODO
      'XXX',
      arg.apply(LambdaExpr(self.sexp[3])).sexp
    ])

  def apply(self, arg):
    assert isinstance(arg, LambdaExpr)
    arg = arg.renumber_from(self.next_var)
    #print 'apply', self, arg
    if self.sexp[0] == self.LAMBDA:
      assert self.sexp[1][0] == '$'
      # TODO check type
      result = self.__apply_inner(self.sexp[3], self.sexp[1], arg)
      #print '>>>', result
      return LambdaExpr(self.__apply_inner(self.sexp[3], self.sexp[1], arg))
    else:
      assert self.is_atom()
      return LambdaExpr([self.sexp, arg.sexp])

  def __apply_inner(self, expr, var, arg):
    assert not isinstance(expr, LambdaExpr)
    assert not isinstance(var, LambdaExpr)
    assert isinstance(arg, LambdaExpr)
    #print '  a i', expr, var, arg
    if isinstance(expr, list):
      if expr[0] in self.SPECIALS:
        expr_head = expr[:2]
        expr_args = expr[2:]
      else:
        expr_head = expr[:1]
        expr_args = expr[1:]
      on_expr_args = [self.__apply_inner(a, var, arg) for a in expr_args]
      if expr_head[0] == var:
        assert len(expr_head) == 1
        #assert len(expr_args) == 1
        r = arg
        for i in range(len(expr_args)):
          r = r.apply(LambdaExpr(on_expr_args[i]))
        #return arg.apply(LambdaExpr(on_expr_args[0]))
        #print '  back', r
        return r.sexp
      else:
        #print '  back', expr_head + on_expr_args
        return expr_head + on_expr_args
    else:
      if expr == var:
        #print '  back', arg
        return arg.sexp
      else:
        #print '  back', expr
        return expr


if __name__ == '__main__':
  import sys
  for line in sys.stdin:
    if line[0] != '(':
      continue
    lam = LambdaExpr.from_string(line)
    print lam.__ustr__()
