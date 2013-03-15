"""
Utility methods for turning a hypergraph node label into a feature vector.
(The resulting vector is suitable for feeding to a semiring.)
"""

def identity(label):
  return label
