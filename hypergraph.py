import math_utils as mu
import dict_utils as du
import math
import itertools

class Hypergraph:
  """
  A directed acyclic hypergraph representing a packed forest of derivations.
  Every Hypergraph object corresponds to one node and one rule application.
  Outgoing edges from this node are specified by their tails (i.e. set of
  nodes).
  """

  def __init__(self, label, edges):
    self.label = label
    self.edges = edges

    self.alpha = None
    self.beta = None
    self.__outside_edges = None

  def __repr__(self):
    return 'Hypergraph{%s}' % (self.label,)

  def enumerate(self):
    if not self.edges:
      yield (self.label,)
    for edge in self.edges:
      child_enumerators = [g.enumerate() for g in edge]
      product_enumerator = itertools.product(*child_enumerators)
      for p in product_enumerator:
        yield (self.label, p)
  
  def inside(self, feat, semiring):
    """
    Cleans up any earlier computation, then runs the Inside algorithm.
    """
    self.__reset_inside_outside()
    self.__inside(feat, semiring)

  def inside_outside(self, feat, semiring):
    """
    Cleans up any earlier computation, then runs the Inside-Outside algorithm.
    """
    self.__add_outside_edges()
    self.__reset_inside_outside()
    self.__inside(feat, semiring)
    self.__outside(feat, semiring)

  def __add_outside_edges(self):
    """
    Labels nodes with their parents and siblings (used for computing beta values
    in the Outside algorithm).
    """
    if self.__outside_edges != None:
      return
    for edge in self.edges:
      for hg in edge:
        hg.__add_outside_edges()
        outside_edge = (self, [i for i in edge if i != hg])
        if hg.__outside_edges == None:
          hg.__outside_edges = []
        hg.__outside_edges.append(outside_edge)

  def __reset_inside_outside(self):
    """
    Forgets any previously-computed alpha and beta values.
    """
    if self.alpha == None:
      assert self.beta == None
      return

    for edge in self.edges:
      for hg in edge:
        hg.__reset_inside_outside()
    self.alpha = None
    self.beta = None

  def __inside(self, feat, semiring):
    if self.alpha != None:
      # we've already computed this node
      return

    # precompute the value of the feature function here
    feat_value = feat(self.label)

    if not self.edges:
      # this is a leaf
      self.alpha = feat_value
      return

    # make sure all descendants get computed first
    for edge in self.edges:
      for hg in edge:
        hg.__inside(feat, semiring)

    to_add = []
    for edge in self.edges:
      to_multiply = [feat_value] + [hg.alpha for hg in edge]
      product = semiring.prod_op(to_multiply)
      to_add.append(product)
    self.alpha = semiring.sum_op(to_add)

  def __outside(self, feat, semiring):
    if self.beta != None:
      # we've already computed this node
      return
    if self.__outside_edges != None and \
       any(parent.beta == None for parent, siblings in self.__outside_edges):
      # we're not ready to compute here yet---wait for all parents to finish.
      # TODO add comment justifying this approach vs. usual topo-sort
      return

    if self.__outside_edges == None:
      # this is the root
      self.beta = semiring.one()
    else:
      to_add = []
      for parent, siblings in self.__outside_edges:
        to_multiply = [feat(parent.label)] + [i.alpha for i in siblings] + \
                      [parent.beta]
        product = semiring.prod_op(to_multiply)
        to_add.append(product)

      assert len(to_add) > 0
      self.beta = semiring.sum_op(to_add)

    for edge in self.edges:
      for hg in edge:
        hg.__outside(feat, semiring)
