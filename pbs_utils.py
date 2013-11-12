import tarfile
import os

def make_tarball(root, dest, ignore=[]):

  assert dest[-7:] == '.tar.gz'
  arcname = os.path.basename(dest)[:-7]

  def filter_fn(f):
    if f.name[len(arcname)+1:] in ignore:
      return None
    return f

  with tarfile.open(dest, 'w:gz', dereference=True) as tarball:
    tarball.add(root, arcname=arcname, filter=filter_fn)

