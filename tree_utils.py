def format_tree(tree, depth=0):
  if len(tree) == 1:
    return '  ' * depth + str(tree)
  child_strings = [format_tree(c, depth+1) for c in tree[1]]
  return '%s%s\n%s' % ('  ' * depth, tree[0], '\n'.join(child_strings))
