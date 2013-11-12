from nlp_tools.list_utils import flatten
from nlp_tools.string_utils import parse_bracketed
import logging

class LambdaExpr:

  LAMBDA = 'lambda'
  UNICODE_LAMBDA = u'\u03bb';
  ALL_LAMBDAS = (LAMBDA, UNICODE_LAMBDA, '\\', 'lambda')
  FNS_E = ('argmin', 'argmax', 'the')
  FNS_T = ('exists', 'and', 'not', '>', 'or', '<')
  FNS_I = ('count', 'sum')
  FNS = FNS_E + FNS_T + FNS_I

  SPECIALS_E_IN = ('argmin', 'argmax', 'the', 'exists', 'count')
  SPECIALS = SPECIALS_E_IN

  def __init__(self, sexp, types = None):
    self.sexp = sexp
    if isinstance(sexp, list):
      toks = list(flatten(sexp))
    else:
      toks = [sexp]
    #varz = [int(t[1:]) for t in toks if t[0] == '$']
    if types:
      self.types = dict(types)
    else:
      self.types = {}
    self.next_var = 0
    for i in range(len(toks)):
      tok = toks[i]
      if tok[0] == '$' and tok not in self.types:
        self.next_var = max(self.next_var, int(tok[1:]) + 1)
        if toks[i-1] == self.LAMBDA:
          self.types[tok] = toks[i+1]
        elif toks[i-1] in self.SPECIALS_E_IN:
          self.types[tok] = 'e'
        else:
          #logging.warn(types)
          #logging.warn('unknown type: %s', tok)
          self.types[tok] = 'UNK'
          #print self.sexp
          #print self.types
          #print 'WHAT?'
          #exit()

    self.typ = self.compute_type(sexp)
    
    #if types:
    #  self.next_var = max(types.keys) + 1
    #else:
    #  self.next_var = 0

  def compute_type(self, sexp):
    if isinstance(sexp, list):
      if sexp[0] == self.LAMBDA:
        return (sexp[2], self.compute_type(sexp[3]))
      elif sexp[0] in self.FNS_E:
        return 'e'
      elif sexp[0] in self.FNS_T:
        return 't'
      elif sexp[0] in self.FNS_I:
        return 'i'
      elif sexp[0] in self.types:
        return self.types[sexp[0]][-1]
      else:
        parts = sexp[0].split(':')
        if len(parts) != 2:
          logging.warn("not sure what to do with %s", sexp)
          exit()
        ftype = parts[1]
        if ftype not in ('e', 't', 'i'):
          #logging.warn("unrecognized type: %s", ftype)
          return 'e'
        return ftype
    else:
      if sexp in self.types:
        return self.types[sexp]
      else:
        assert len(sexp.split(':')) == 2
        return 'e'

  @classmethod
  def parse_type(cls, typ):
    typ = typ.replace('<', '< ')
    typ = typ.replace('>', ' >')
    typ = typ.replace(',', ' ')
    toks = typ.split()
    toks.reverse()

    if len(toks) == 1:
      return toks[0]
    
    list_stack = []
    this_list = None
    while toks:
      tok = toks.pop()
      if tok == '<':
        this_list = []
        list_stack.append(this_list)
      elif tok == '>':
        last_list = tuple(list_stack.pop())
        if not list_stack:
          assert not toks
          return last_list
        else:
          this_list = list_stack[-1]
          this_list.append(last_list)
      else:
        this_list.append(tok)
    assert False

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
    type_next = 0
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
        if type_next == 2:
          type_next = 1
        elif type_next == 1:
          tok = cls.parse_type(tok)
          type_next = 0
        if tok in cls.ALL_LAMBDAS:
          tok = cls.LAMBDA
          type_next = 2
        this_list.append(tok)
    assert False

  def __str__(self):
    return self.__str_inner(self.sexp)

  def __repr__(self):
    return str(self)

  def __ustr__(self):
    return self.__str__().replace(self.LAMBDA, self.UNICODE_LAMBDA)

  def __str_inner(self, sexp):
    if isinstance(sexp, list):
      return '(%s)' % ' '.join([self.__str_inner(tok) for tok in sexp])
    elif isinstance(sexp, tuple):
      # this is a type
      return str(sexp).replace('(', '<').replace(')', '>').replace("'",
          '').replace(' ', '')
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
    nsexp, ntypes = self.__renumber_from_inner(start, bound, self.sexp,
        self.types)
    return LambdaExpr(nsexp, types=ntypes)
    #return LambdaExpr(self.__renumber_from_inner(start, bound, self.sexp),
    #    types=self.types)

  def __renumber_from_inner(self, start, bound, sexp, types):
    if isinstance(sexp, list):
      ret = [self.__renumber_from_inner(start, bound, s, types) for s in sexp]
      ntypes = {}
      for s, t in ret:
        ntypes.update(t)
      return ([s for s, t in ret], ntypes)
    #if sexp[0] == '$':
    if sexp in bound:
      ratom = '$%d' % (int(sexp[1:]) + start)
      ntypes = dict(types)
      del ntypes[sexp]
      ntypes[ratom] = types[sexp]
      return ratom, ntypes
    else:
      return sexp, {sexp: types[sexp]} if sexp in types else {}
    
  def compose(self, arg):
    assert isinstance(arg, LambdaExpr)
    #assert not self.is_atom() and self.sexp[0] == self.LAMBDA
    assert not self.is_atom()
    assert self.sexp[0] == self.LAMBDA

    return LambdaExpr([
      self.LAMBDA,
      self.sexp[1],
      self.sexp[2],
      arg.apply(LambdaExpr(self.sexp[3], types={self.sexp[1]: self.sexp[2]})).sexp
    ])

  def apply(self, arg):
    assert isinstance(arg, LambdaExpr)

    arg = arg.renumber_from(self.next_var)
    #print 'apply', self, arg
    if self.sexp[0] == self.LAMBDA:
      assert self.sexp[1][0] == '$'
      #assert self.sexp[2][0] == arg.sexp[2]

      myintype = self.sexp[2]
      argtype = arg.typ

      print '\n'
      print '!!!'
      print self.sexp
      print myintype

      print arg.sexp
      print argtype

      #print 'type agreement', argtype == myintype
      assert argtype == myintype

      #print 'ok'

      #if isinstance(arg.sexp, list):
      #  if arg.sexp[0] == self.LAMBDA:
      #    argtype = arg.sexp[2]
      #  elif arg.sexp[0] in SPECIALS_E:
      #    argtype = 'e'
      #  elif arg.sexp[0] in SPECIALS_T:
      #    argtype = 't'
      #  elif arg.sexp[0] in SPECIALS_I:
      #    argtype = 'i'
      #  else:
      #    print '>>> TODO'
      #    print arg.sexp[0]
      #    exit()
      #else:
      #  if arg.sexp in self.types:
      #    argtype = self.types[arg.sexp]
      #  else:
      #    parts = arg.sexp.split(':')
      #    print 'e'
      #    #if len(parts) != 2:
      #    #  logging.error("don't know what to do with %s", arg.sexp)
      #    #argtype = parts[1]

      #print argtype

      #result = self.__apply_inner(self.sexp[3], self.sexp[1], arg)
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
          #print 'xxx'
          #print arg
          #print on_expr_args[i]
          #print self.types
          r = r.apply(LambdaExpr(on_expr_args[i], types=self.types))
          #print 'done', r
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
