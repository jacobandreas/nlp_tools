import numpy as np
from scipy import sparse

class FeatureSet(object):

  def __init__(self, featurizer=lambda x:x):
    self.feature_dict = {}
    self.featurizer = featurizer

  def register(self, ex):
    feats = self.featurizer(ex)
    for feat in feats:
      if feat not in self.feature_dict:
        self.feature_dict[feat] = len(self.feature_dict)
    return self.represent(ex)

  def represent(self, ex):
    feats = self.featurizer(ex)
    vec = sparse.lil_matrix((len(self.feature_dict), 1))
    for feat in feats:
      if feat in self.feature_dict:
        vec[self.feature_dict[feat],0] += 1
    return sparse.csc_matrix(vec)

  def __len__(self):
    return len(self.feature_dict)
