#!/usr/bin/env python2

import termcolor

import math_utils
import dict_utils
import semiring
import feature
import hypergraph

def log_file(name):
  print name

def log_function(name):
  print '  %s' % name

def log_input(inpt):
  print '    %s' % str(inpt)

def log_expected(exp):
  print '      <- %s' % str(exp)

def log_result(output, status):
  status_str = 'OK' if status else 'FAIL'
  status_color = 'green' if status else 'red'
  print '      -> %s' % str(output)
  termcolor.cprint('      %s' % status_str, status_color)

def test(test, fun, args, expected):
  log_input(args)
  log_expected(expected)
  real = fun(*args)
  log_result(real, test(real, expected))

def test_eq(fun, args, expected):
  return test(lambda r,e: r==e, fun, args, expected)

def test_eq_float(fun, args, expected, tolerance=1e-5):
  return test(lambda r,e: abs(r-e) < tolerance, fun, args, expected)

# math utils

log_file('math_utils.py')
log_function('logspace_sum')
test_eq_float(math_utils.logspace_sum, ([1.0],), 1.0)
test_eq_float(math_utils.logspace_sum, ([0.0, 0.0],), 0.693147)
test_eq_float(math_utils.logspace_sum, ([0.0, -1.0],), 0.313262)

# dict utils

log_file('dict_utils.py')
log_function('d_sum')
test_eq(dict_utils.d_sum,
        ([{'a': 1, 'b': 2}, {'b': -2, 'c': 3}],),
        {'a': 1, 'c': 3})

log_function('d_elt_prod')
test_eq(dict_utils.d_elt_prod,
        ([{'a': 1, 'b': 2}, {'b': -2, 'c': 3}],),
        {'b': -4})

log_function('d_dot_prod')
test_eq(dict_utils.d_dot_prod,
        ({'a': 1, 'b': 2}, {'a': -1, 'b': 2, 'c': 7}),
        3)

# semiring

log_file('semiring.py')
sr = semiring.LogLinearExpectationSemiring()

log_function('sum_op')
test_eq(sr.sum_op, ([sr.zero(), sr.one()],), sr.one())

log_function('prod_op')
test_eq(sr.prod_op, ([sr.zero(), sr.one()],), sr.zero())

# feature

# hypergraph

log_file('hypergraph.py')
a = hypergraph.Hypergraph('a', ())
b = hypergraph.Hypergraph('b', ())
c = hypergraph.Hypergraph('c', ((a,b),(b,a)))
d = hypergraph.Hypergraph('d', ((c,a),(c,b)))
sr = semiring.DebugSemiring()

log_function('inside')
d.inside(feature.identity, sr)
test_eq(lambda hg: hg.alpha, (c,), 
        '((c) AND (a) AND (b)) OR ((c) AND (b) AND (a))')

log_function('outside')
c.inside_outside(feature.identity, sr)
test_eq(lambda hg: hg.beta, (a,),
        '((c) AND (b)) OR ((c) AND (b))')
