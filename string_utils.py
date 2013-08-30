def parse_bracketed(lb, rb, bracketed, delim = None):
  toks = bracketed.replace(lb, lb + ' ')
  toks = toks.replace(rb, ' ' + rb)
  if delim:
    toks = toks.replace(delim, ' ')
  toks = toks.split()
  toks.reverse()

  if len(toks) == 1:
    return toks[0]

  list_stack = []
  this_list = None
  while toks:
    tok = toks.pop()
    if tok == lb:
      this_list = []
      list_stack.append(this_list)
    elif tok == rb:
      last_list = tuple(list_stack.pop())
      if not list_stack:
        assert not toks
        return last_list
      else:
        this_list = list_stack[-1]
        this_list.append(last_list)
    else:
      this_list.append(tok)
  assert False
