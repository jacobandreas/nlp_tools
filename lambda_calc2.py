from  nlp_tools.list_utils import flatten

def is_var(tok):
  return isinstance(tok, str) and tok[0] == '$'

def var_no(tok):
  return int(tok[1:])

class LambdaExpr:

  LAMBDA = 'lambda'
  UNICODE_LAMBDA = u'\03bb'

  RETURN_TYPES = {
    'argmin': 'e',
    'argmax': 'e',
    'the': 'e',
    'exists': 't',
    'forall': 't',
    'and', 't',
    'or', 't',
    'not', 't',
    '>', 't',
    '<', 't',
    'count', 'i',
    'sum', 'i',
  }

  VARIABLE_TYPES = {
    'argmin': 'e',
    'argmax': 'e',
    'the': 'e',
    'exists': 'e',
    'forall': 'e',
    'count': 'e',
  }

  def __init__(self, sexp, types = None):
    # save sexp
    self.sexp = sexp

    # setup existing type mapping
    if types:
      self.types = dict(types)
    else:
      self.types = {}

    # extract new variable and type info
    self.next_var = 0
    if not isinstance(sexp, list):
      return
    toks = list(flatten(sexp))
    for i in range(len(toks)):
      tok = toks[i]
      # is this a nonvariable, or a variable we already know about?
      if not is_var(tok) or tok in self.types:
        continue
      self.next_var = max(self.next_var, var_no(tok) + 1)
      if toks[i-1] == self.LAMBDA:
        # if it's a lambda, we can read the type directly off the expression
        self.types[tok] = toks[i+1]
      elif toks[i-1] in self.VARIABLE_TYPES:
        # if it's a special form, we already know the type
        self.types[tok] = self.VARIABLE_TYPES[toks[i-1]]
      else:
        # not sure what do do with this
        self.types[tok] = 'UNK'
        logging.warn('unknown type: %s', tok)

  def compute_type(self, sexp):
    if not isinstance(sexp, list):
      # sexp is either a variable or a known atom
      if sexp in self.types:
        return self.types[sexp]
      else:
        assert len(sexp.split(':')) == 2
        return 'e'
    # if we got to here, sexp is a list
    fname = sexp[0]
    if fname == self.LAMBDA:
      return (sexp[2], self.compute_type(sexp[3]))
    if fname in self.RETURN_TYPES:
      return self.RETURN_TYPES[sexp[0]]
    if fname in self.types:
      return self.types[fname][-1]
    fname_parts = fname.split(':')
    assert len(fname_parts) == 2
    ftype = fname_parts[1]
    if ftype not in ('e', 't', 'i'):
      # assume all unknown types are fancy entities
      # TODO there's a more principled way to do this
      return 'e'
    return ftype

  def __str__(self):
    return self.__str_inner(self.sexp)

  def __repr__(self):
    return str(self)

  def __str_inner(self, sexp):
    if isinstance(sexp, list):
      return '(%s)' % ' '.join([self.__str_inner(tok) for tok in sexp])
    if isinstance(sexp, tuple):
      # this is a type
      # TODO cleaner
      return str(sexp).replace('(', '<').replace(')', '>').replace("'", '').replace(' ', '')
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

