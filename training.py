"""
Training algorithms.
"""

from math import log
import dict_utils as du
import math_utils as mu
from semiring import ExpectationSemiring
from collections import defaultdict
import logging

def em(rules, hypergraphs, group_getter, iters=10):
  """
  Runs the Expectation-Maximization for parse forests on the given data.
  `hypergraphs` is a set of (pre-parsed) training examples where each node has
  been labeled with one of the rules in `rules`. `group-getter` takes a rule
  object as input and returns an object (typically the rule RHS symbol) shared
  by a group of rules whose probabilities should be constrained to sum to 1.
  """

  # precompute normalization groups
  normalizing_groups = defaultdict(list)
  for rule in rules:
    normalizing_groups[group_getter(rule)].append(rule)

  # compute initial weights
  unnormalized_weights = {}
  for rule in rules:
    unnormalized_weights[rule] = 0
  weights = {}
  for key in unnormalized_weights:
    norm = mu.logspace_sum([unnormalized_weights[k] for k in
                            normalizing_groups[group_getter(key)]])
    weights[key] = mu.logspace_prod([unnormalized_weights[key], -norm])

  logging.info('Running EM for %d iterations.', iters)

  # run EM
  for i in range(iters):
    def scorer(label):
      pr = weights[label]
      return (pr, {label: pr})
    semiring = ExpectationSemiring()

    prob = 0
    counts = {}
    for hg in hypergraphs:
      hg.inside(scorer, semiring)
      prob_single, counts_single = hg.alpha
      prob = mu.logspace_prod([prob, prob_single])
      ncounts = du.d_logspace_scalar_prod(-prob_single, counts_single)
      counts = du.d_logspace_sum([counts, ncounts])

    weights = {}
    for key in counts:
      norm = mu.logspace_sum([counts[k] for k in
                              normalizing_groups[group_getter(key)]
                              if k in counts])
      weights[key] = mu.logspace_prod([counts[key], -norm])

    logging.info('Iteration %d. NLL: %f.', i, prob)
