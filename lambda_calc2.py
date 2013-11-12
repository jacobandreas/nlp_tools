from nlp_tools.list_utils import flatten, lol_to_tot, tot_to_lol
from nlp_tools.string_utils import parse_bracketed
import itertools

def is_var(tok):
  return isinstance(tok, str) and tok[0] == '$'

def var_no(tok):
  return int(tok[1:])

class ReductionException(Exception):
  pass

class LambdaExpr:

  LAMBDA = 'lambda'
  UNICODE_LAMBDA = u'\03bb'

  RETURN_TYPES = {
    'and': 't',
    'or': 't',
    'capital:t': 't'
  }

  TYPE_SIGNATURES = {
    'argmin': (None, 'e'),
    'argmax': (None, 'e'),
    'the': (None, 'e'),
    'exists': (None, 't'),
    'forall': (None, 't'),
    'and': None,
    'or': None,
    'not': ('t', 't'),
    '>': ('e', ('e', 't')),
    '<': ('e', ('e', 't')),
    'count': (None, 'e'),
    'sum': (None, 'e'),
    'loc:t': ('e', ('e', 't')),
    'next_to:t': ('e', ('e', 't')),
    'state:t': ('e', 't'),
    'river:t': ('e', 't'),
    'capital:c': ('e', 'e'),
    'population:t': ('e', ('e', 't')),
    'lake:t': ('e', 't'),
    'population:i': ('e', 'e'),
    'named:t': ('e', ('e', 't')),
    'capital:t': None,
    'size:i': ('e', 'e'),
    'city:t': ('e', 't'),
    'elevation:i': ('e', 'e'),
    'len:i': ('e', 'e'),
    'area:i': ('e', 'e'),
    'density:i': ('e', 'e'),
    'place:t': ('e', 't'),
    'equals:t': ('e', ('e', 't')),
    'town:t': ('e', 't'),
    'mountain:t': ('e', 't'),
    'major:t': ('e', 't'),
    'density:t': ('e', ('e', 't')),
    'in:t': ('e', ('e', 't')),
  }

  VARIABLE_TYPES = {
    'argmin': 'e',
    'argmax': 'e',
    'the': 'e',
    'exists': 'e',
    'forall': 'e',
    'count': 'e',
    'sum': 'e',
  }

  INTERNALLY_SPLITTABLE = {'and', 'or'}

  @classmethod 
  def from_string(cls, string):
    sexp = parse_bracketed('(', ')', string)
    sexp = cls.__from_string_inner(sexp)
    return LambdaExpr(sexp)

  @classmethod
  def __from_string_inner(cls, sexp):
    if not isinstance(sexp, tuple):
      return sexp
    if sexp[0] == cls.LAMBDA:
      return (sexp[0], sexp[1], parse_bracketed('<', '>', sexp[2], ','), 
              cls.__from_string_inner(sexp[3]))
    return tuple(cls.__from_string_inner(child) for child in sexp)

  def __hash__(self):
    return hash(self.sexp)

  def __eq__(self, other):
    return self.sexp == other.sexp

  def __init__(self, sexp, types = None):
    # save sexp
    self.sexp = sexp

    # setup existing type mapping
    if types:
      self.types = dict(types)
    else:
      self.types = {}

    # extract new variable and type info
    #self.next_var = 0
    #if isinstance(sexp, tuple):
    #  toks = list(flatten(sexp))
    #  for i in range(len(toks)):
    #    tok = toks[i]
    #    # is this a nonvariable, or a variable we already know about?
    #    if not is_var(tok) or tok in self.types:
    #      continue
    #    self.next_var = max(self.next_var, var_no(tok) + 1)
    #    if toks[i-1] == self.LAMBDA:
    #      # if it's a lambda, we can read the type directly off the expression
    #      self.types[tok] = toks[i+1]
    #    elif toks[i-1] in self.VARIABLE_TYPES:
    #      # if it's a special form, we already know the type
    #      self.types[tok] = self.VARIABLE_TYPES[toks[i-1]]
    #    else:
    #      # not sure what do do with this
    #      self.types[tok] = 'UNK'
    #      logging.warn('unknown type: %s', tok)
    self.collect_types(self.sexp)
    int_keys = [var_no(k) for k in self.types]
    if int_keys:
      self.next_var = max(int_keys) + 1
    else:
      self.next_var = 0

    self.typ = self.compute_type(sexp)

  def collect_types(self, sexp):
    recurse_on = []
    if sexp[0] == self.LAMBDA:
      #assert sexp[1] not in self.types
      self.types[sexp[1]] = sexp[2]
      recurse_on = sexp[3:]
    elif sexp[0] in self.VARIABLE_TYPES:
      #assert sexp[1] not in self.types
      self.types[sexp[1]] = self.VARIABLE_TYPES[sexp[0]]
      recurse_on = sexp[2:]
    elif isinstance(sexp, tuple):
      recurse_on = sexp

    for nsexp in recurse_on:
      self.collect_types(nsexp)

  def normalize_vars(self):
    list_sexp = tot_to_lol(self.sexp)
    ntypes = {}
    self.__normalize_vars(list_sexp, {}, [0], ntypes, self.types)
    nsexp = lol_to_tot(list_sexp)
    return LambdaExpr(nsexp, types=ntypes)

  def __normalize_vars(self, list_sexp, renamings, next_var, newtypes, oldtypes):
    var_pos = []
    recurse_on = []
    if list_sexp[0] == self.LAMBDA:
      var_pos = [1]
      recurse_on = list_sexp[3:]
      recurse_on_offset = 3
    elif isinstance(list_sexp[0], str) and list_sexp[0] in self.VARIABLE_TYPES:
      var_pos = [1]
      recurse_on = list_sexp[2:]
      recurse_on_offset = 2
    elif isinstance(list_sexp, list):
      recurse_on = list_sexp
      recurse_on_offset = 0

    for i, ssexp in enumerate(recurse_on):
      if is_var(ssexp):
        var_pos.append(i + recurse_on_offset)
        
    #if var_pos != None:
    for vp in var_pos:
      var = list_sexp[vp]
      #assert var not in renamings
      if var not in renamings:
        nvar = '$%s' % (next_var[0])
        renamings[var] = nvar
        newtypes[nvar] = oldtypes[var]
        next_var[0] += 1
        #print '* %s -> %s' % (var, nvar)
      list_sexp[vp] = renamings[var]

    for nsexp in recurse_on:
      self.__normalize_vars(nsexp, renamings, next_var, newtypes, oldtypes)

    if isinstance(list_sexp[0], str) and list_sexp[0] in self.INTERNALLY_SPLITTABLE:
      list_sexp[1:] = sorted(list_sexp[1:])
      
  def compute_type(self, sexp):
    if not isinstance(sexp, tuple):
      if sexp in self.types:
        return self.types[sexp]
      elif is_var(sexp):
        return 'UNK'
      elif sexp in self.TYPE_SIGNATURES:
        #assert sexp in self.RETURN_TYPES
        #assert sexp in self.ARG_TYPES
        #return (self.ARG_TYPES[sexp], self.RETURN_TYPES[sexp])
        if self.TYPE_SIGNATURES[sexp]:
          return self.TYPE_SIGNATURES[sexp]
        elif self.RETURN_TYPES[sexp]:
          return ('UNK', self.RETURN_TYPES[sexp])
        else:
          return ('UNK', 'UNK')
      else:
        return 'e'

    fname = sexp[0]
    if fname == self.LAMBDA:
      return (sexp[2], self.compute_type(sexp[3]))
    return self.compute_type(sexp[0])[1]

  #def compute_type(self, sexp):
  #  if not isinstance(sexp, tuple):
  #    # sexp is either a variable or a known atom
  #    if sexp in self.types:
  #      return self.types[sexp]
  #    elif is_var(sexp):
  #      return 'UNK'
  #    elif sexp in self.RETURN_TYPES:
  #      return self.RETURN_TYPES[sexp]
  #      # TODO this shouldn't need to happen twice!
  #    else:
  #      assert len(sexp.split(':')) == 2
  #      print '1', sexp
  #      return 'e'
  #  # if we got to here, sexp is a tuple (i.e. an application or special form)
  #  fname = sexp[0]
  #  if fname == self.LAMBDA:
  #    return (sexp[2], self.compute_type(sexp[3]))
  #  if fname in self.RETURN_TYPES:
  #    return self.RETURN_TYPES[sexp[0]]
  #  if fname in self.types:
  #    return self.types[fname][-1]
  #  if is_var(fname):
  #    return 'UNK'
  #  if isinstance(fname, tuple):
  #    ret = self.types[fname[0]]
  #    for i in range(len(fname)-1):
  #      ret = ret[1]
  #    return ret
  #  fname_parts = fname.split(':')
  #  assert len(fname_parts) == 2
  #  ftype = fname_parts[1]
  #  print 2, fname
  #  if ftype not in ('e', 't'):
  #    # assume all unknown types are fancy entities
  #    # TODO there's a more principled way to do this
  #    return 'e'
  #  return ftype

  def __str__(self):
    return self.__str_inner(self.sexp)

  def __repr__(self):
    return str(self)

  def __str_inner(self, sexp):
    if isinstance(sexp, tuple):
      return '(%s)' % ' '.join([self.__str_inner(tok) for tok in sexp])
    # TODO pretty types
    return sexp

  def is_lambda(self):
    return isinstance(self.sexp, tuple) and self.sexp[0] == self.LAMBDA

  def is_atom(self):
    return not isinstance(self.sexp, tuple)

  def all_vars(self):
    return self.__all_vars_inner(self.sexp)

  def __all_vars_inner(self, sexp):
    if isinstance(sexp, tuple):
      return set().union(*list(self.__all_vars_inner(s) for s in sexp))
    if is_var(sexp):
      return {sexp}
    return set()

  def free_vars(self):
    return self.all_vars() - self.bound_vars()

  def bound_vars(self):
    return self.__bound_vars_inner(self.sexp)

  def __bound_vars_inner(self, sexp):
    if not isinstance(sexp, tuple):
      return set()
    if sexp[0] == self.LAMBDA:
      # add my variable and descend on body
      return set([sexp[1]]) | self.__bound_vars_inner(sexp[3])
    if sexp[0] in self.VARIABLE_TYPES:
      # add my variable and descend on all arguments
      r = set([sexp[1]])
      for t in sexp[2:]:
        r |= self.__bound_vars_inner(t)
      return r
    # if this is a regular function call, just recurse
    r = set()
    for t in sexp[1:]:
      r |= self.__bound_vars_inner(t)
    return r

  def __renumber_from(self, start):
    bound = self.bound_vars()
    nsexp, ntypes = self.__renumber_from_inner(start, bound, self.sexp,
        self.types)
    return LambdaExpr(nsexp, types=ntypes)

  # returns a (sexp, type dictionary) pair
  def __renumber_from_inner(self, start, bound, sexp, types):
    if isinstance(sexp, tuple):
      ret = tuple(self.__renumber_from_inner(start, bound, s, types) for s in sexp)
      ntypes = {}
      for s, t in ret:
        ntypes.update(t)
      return (tuple(s for (s, t) in ret), ntypes)
    if sexp in bound:
      ratom = '$%d' % (var_no(sexp) + start)
      ntypes = dict(types)
      del ntypes[sexp]
      ntypes[ratom] = types[sexp]
      return ratom, ntypes
    else:
      return sexp, {sexp: types[sexp]} if sexp in types else {}

  def apply(self, arg):
    #print 'apply called', self.types
    assert isinstance(arg, LambdaExpr)
    # prevent variable name collisions
    arg = arg.__renumber_from(self.next_var)
    if self.sexp[0] == self.LAMBDA:
      expected_arg_type = self.sexp[2]
      arg_type = arg.typ
      #assert expected_arg_type == arg_type
      if expected_arg_type != arg_type:
        raise ReductionException('type mismatch')
      #result = self.__apply_inner(self.sexp[3], self.sexp[1], arg)
      #print result
      return LambdaExpr(self.__apply_inner(self.sexp[3], self.sexp[1], arg))
    else:
      # this is either an atom or an application involving a higher-order
      # function
      # if application of a higher-order function, uncurry arguments
      if isinstance(self.sexp, tuple):
        return LambdaExpr(self.sexp + (arg.sexp,), types=self.types)
      else:
        return LambdaExpr((self.sexp, arg.sexp), types=self.types)

  def __apply_inner(self, expr, var, arg):
    #print 'ai', expr, var, arg
    # expr is the expression in which substitution is taking place
    # var is the variable to be replaced with the argument
    # arg is the argument to substitute in
    # check typing---expr is a bare list, var is a string and arg is a LambdaExpr
    assert isinstance(var, str)
    assert isinstance(arg, LambdaExpr)
    if isinstance(expr, tuple):
      if expr[0] == self.LAMBDA:
        expr_head = expr[:3]
        expr_args = expr[3:]
      elif expr[0] in self.VARIABLE_TYPES:
        expr_head = expr[:2]
        expr_args = expr[2:]
      else:
        expr_head = expr[:1]
        expr_args = expr[1:]
      # recursively replace occurrences of the argument throughout the body
      applied_to_args = tuple(self.__apply_inner(a, var, arg) for a in expr_args)
      #if expr_head[0] == var:
      if len(expr_head) == 1:
        # we're replacing a function which is called in this expression
        ### # sanity check: make sure it's not a special form
        ### assert len(expr_head) == 1
        # now we should try to apply it to its arguments
        # if there are multiple arguments we should assume the function has been
        #   curried
        r = LambdaExpr(self.__apply_inner(expr_head[0], var, arg),
                       types=self.types)
        for i in range(len(applied_to_args)):
          r = r.apply(LambdaExpr(applied_to_args[i], types=self.types))
        #print expr, '!', var, '!', arg, '!', r.sexp
        return r.sexp
      else:
        # no need for application here
        return expr_head + applied_to_args
    else:
      if expr == var:
        # the variable occurs as an argument---just replace it
        return arg.sexp
      else:
        # nothing to do here
        return expr

  def compose(self, arg):
    # sanity checks
    assert isinstance(arg, LambdaExpr)
    assert not arg.is_atom()
    assert not self.is_atom()
    assert self.sexp[0] == self.LAMBDA
    assert arg.sexp[0] == self.LAMBDA

    arg = arg.__renumber_from(self.next_var)

    #return LambdaExpr([
    #  self.LAMBDA,
    #  self.sexp[1],
    #  self.sexp[2],
    #  arg.apply(LambdaExpr(self.sexp[3], types={self.sexp[1]: self.sexp[2]})).sexp

    # TODO check that typing behaves as expected here
    return LambdaExpr((
      self.LAMBDA,
      arg.sexp[1],
      arg.sexp[2],
      self.apply(LambdaExpr(arg.sexp[3], types={arg.sexp[1]: arg.sexp[2]})).sexp
    ))

  def splits(self):
    for subexpr in self.subexprs():
      yield self.split_on(subexpr)

  def compute_fn_type_in(self, expr, sexp):
    if sexp[0] == expr:
      ret = self.RETURN_TYPES[expr]
      for arg in sexp[1:]:
        ret = (self.compute_type(arg), ret)
      return ret

    if isinstance(sexp, tuple):
      for ssexp in sexp:
        ret = self.compute_fn_type_in(expr, ssexp)
        if ret:
          return ret
    return None

  def split_on(self, expr):
    #print self
    expr = LambdaExpr(expr, types = dict(self.types))

    fvars = sorted(expr.free_vars())

    nvar = '$%d' % self.next_var

    if fvars:
      nsubexpr = (nvar,) + tuple(fvars)
    else:
      nsubexpr = nvar


    nexpr = expr.sexp
    nexpr_vars = []
    for fvar in fvars:
      #print
      #print fvar
      #print nexpr
      #print self.types
      nexpr = (
          self.LAMBDA,
          fvar,
          self.types[fvar],
          nexpr
      )
      nexpr_vars.append(self.types[fvar])
    nexpr = LambdaExpr(nexpr)

    if nexpr.typ == 'UNK' or isinstance(nexpr.typ, tuple) and 'UNK' in flatten(nexpr.typ):
      nexpr.typ = self.compute_fn_type_in(nexpr.sexp, self.sexp)
    assert nexpr.typ != 'UNK' or isinstance(nexpr.typ, tuple) and 'UNK' not in flatten(nexpr.typ)

    #print nexpr.typ
    #print nexpr_vars
    #print '-'

    nself = self.__replace_in(self.sexp, expr.sexp, nsubexpr)
    if nself == self.sexp:
      print self.sexp
      print expr.sexp
      print nsubexpr
      assert False
    nself = (
        self.LAMBDA,
        nvar,
        nexpr.typ,
        nself
    )

    nself = LambdaExpr(nself)

    nself = nself.normalize_vars()
    nexpr = nexpr.normalize_vars()

    #print self
    #print nself
    #print nexpr
    #print
    return (nself, nexpr)

  def __replace_in(self, sexp, before_sexp, after_sexp):

    if sexp == before_sexp:
      return after_sexp
    if not isinstance(sexp, tuple):
      return sexp

    # special case for and / or
    if before_sexp[0] in self.INTERNALLY_SPLITTABLE and \
        sexp[0] == before_sexp[0] and \
        all(arg in sexp[1:] for arg in before_sexp[1:]):
      excluded_args = [arg for arg in sexp[1:] if arg not in before_sexp[1:]]

      #print sexp
      #print before_sexp
      #print after_sexp
      #exit()
      return (before_sexp[0],) + tuple(excluded_args) + (after_sexp,)

    if sexp[0] == self.LAMBDA:
      expr_head = sexp[:3]
      expr_args = sexp[3:]
    elif sexp[0] in self.VARIABLE_TYPES:
      expr_head = sexp[:2]
      expr_args = sexp[2:]
    else:
      expr_head = []
      expr_args = sexp

    replaced_in_args = tuple(self.__replace_in(arg, before_sexp, after_sexp) for
        arg in expr_args)

    return tuple(expr_head) + replaced_in_args

    #return tuple(expr_head) + sum(list(self.__replace_in(arg, before_sexp,
    #  after_sexp) for arg in expr_args), ())

  def subexprs(self):
    for subexpr in self.__subexprs_inner(self.sexp):
      yield subexpr

  def __subexprs_inner(self, sexp):
    yield sexp
    if not isinstance(sexp, tuple):
      return

    if sexp[0] in self.INTERNALLY_SPLITTABLE:
      for r in range(2,len(sexp)-1):
        for combo in itertools.combinations(sexp[1:], r):
          yield sexp[0:1] + combo

    if sexp[0] == self.LAMBDA:
      sub_sexp_iters = [self.__subexprs_inner(sexp[3])]
    elif sexp[0] in self.VARIABLE_TYPES:
      sub_sexp_iters = [self.__subexprs_inner(arg) for arg in sexp[2:]]
    else:
      sub_sexp_iters = [self.__subexprs_inner(arg) for arg in sexp]

    for ssexp_iter in sub_sexp_iters:
      for val in ssexp_iter:
        yield val
