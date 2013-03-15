#!/usr/bin/env python2

import math_utils
import dict_utils

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
  print '      -> %s %s' % (output, status_str)

def test(test, fun, args, expected):
  log_input(args)
  log_expected(expected)
  real = fun(*args)
  log_result(real, test(real, expected))

def test_eq(fun, args, expected):
  return test(lambda r,e: r==e, fun, args, expected)

def test_eq_float(fun, args, expected, tolerance=1e-5):
  return test(lambda r,e: abs(r-e) < tolerance, fun, args, expected)

log_file('math_utils.py')
log_function('logspace_add')
test_eq_float(math_utils.logspace_add, (1.0,), 1.0)
test_eq_float(math_utils.logspace_add, (0.0, 0.0), 0.693147)
test_eq_float(math_utils.logspace_add, (0.0, -1.0), 0.313262)

log_file('dict_utils.py')
log_function('d_sum')
test_eq(dict_utils.d_sum,
        ({'a': 1, 'b': 2}, {'b': -2, 'c': 3}),
        {'a': 1, 'c': 3})
log_function('d_elt_prod')
test_eq(dict_utils.d_elt_prod,
        ({'a': 1, 'b': 2}, {'b': -2, 'c': 3}),
        {'b': -4})
log_function('d_dot_prod')
test_eq(dict_utils.d_dot_prod,
        ({'a': 1, 'b': 2}, {'a': -1, 'b': 2, 'c': 7}),
        3)
