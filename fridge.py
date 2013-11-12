import logging
from nlp_tools import config
import os
import pickle

logger = logging.getLogger(__name__)

NONE = 0
LOL = 1

LOL_SEPARATOR = ' ||| '

FMT_EXT = 'fridge.txt'
PCL_EXT = 'fridge.pcl'

store = {}

def put(key, value, fmt=NONE):
  if key in store:
    logger.warn('overwriting key `%s`', key)
  store[key] = value

  if fmt:
    txt_path = os.path.join(config.work_dir, '{}.{}'.format(key, FMT_EXT))
    if fmt == LOL:
      write_lol(value, txt_path)

  pcl_path = os.path.join(config.work_dir, '{}.{}'.format(key, PCL_EXT))
  write_pcl(value, pcl_path)

def get(key):
  return store[key]

def get_all_from_disk(path):
  for name in os.listdir(path):
    if name[-len(PCL_EXT):] == PCL_EXT:
      key = name[:-len(PCL_EXT)-1]
      with open(os.path.join(path, name)) as read_f:
        put(key, pickle.load(read_f))

def write_lol(v, path):
  with open(path, 'w') as write_f:
    for line in v:
      print >>write_f, ' ||| '.join([str(l) for l in line])

def write_pcl(v, path):
  try:
    with open(path, 'w') as write_f:
      pickle.dump(v, write_f)
  except TypeError:
    logger.warn('failed to pickle %s', v.__class__)
