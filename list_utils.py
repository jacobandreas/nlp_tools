import collections

##http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
#def flatten(l):
#    for el in l:
#        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
#            for sub in flatten(el):
#                yield sub
#        else:
#            yield el

def flatten(l):
  return __flatten_inner(l, l.__class__)

def __flatten_inner(l, typ):
  for el in l:
    if isinstance(el, typ):
      for sub in __flatten_inner(el, typ):
        yield sub
    else:
      yield el

def lol_to_tot(l):
  if not isinstance(l, list):
    return l
  return tuple(lol_to_tot(ll) if isinstance(ll, list) else ll for ll in l)

def tot_to_lol(t):
  if not isinstance(t, tuple):
    return t
  return [tot_to_lol(tt) if isinstance(tt, tuple) else tt for tt in t]
