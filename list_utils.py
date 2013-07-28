import collections

#http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el
