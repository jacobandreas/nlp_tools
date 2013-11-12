import datetime
import logging
import os
import sys
import logging_utils

SEPARATOR = '::'

default_keys = set()
commandline_keys = set()
all_keys = set()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
stream_log_handler = logging.StreamHandler()
stream_log_handler.setFormatter(logging_utils.PrettyFormatter())
root_logger.addHandler(stream_log_handler)

logger = logging.getLogger(__name__)


def coerce_arg(value):
  try:
    return int(value)
  except:
    try:
      return float(value)
    except:
      if value == None:
        return True
      if value.lower() == 'true':
        return True
      if value.lower() == 'false':
        return False
      if value == 'None':
        return None
      return value

def has(k):
  return k in all_keys

def default(k, v):
  if k in default_keys:
    logger.warn('%s has multiple default values', k)

  if k not in all_keys:
    dynamic(k, v)
    default_keys.add(k)

def commandline(k, v):
  if k in commandline_keys:
    logger.warn('%s has multiple command line settings', k, v)

  if k in default_keys:
    logger.info('overriding default value of %s', k)

  dynamic(k, v)
  commandline_keys.add(k)

def dynamic(k, v):

  if SEPARATOR in k:
    raise Exception('Special sequence %s can\'t appear in config key.' %
        SEPARATOR)
  if type(v) not in (str, int, float, tuple, bool, type(None)):
    raise Exception('Unsupported type for {}'.format(v))
  mod = __import__(__name__).config
  all_keys.add(k)
  setattr(mod, k, v)

def get(k):
  mod = __import__(__name__).config
  return getattr(mod, k)

def timestamp():
  return datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

def timestamp_dir(base_dir):
  return os.path.join(base_dir, timestamp())

def dump(path):
  with open(path, 'w') as dump_f:
    max_key_len = max(len(k) for k in all_keys)
    for k in all_keys:
      print >>dump_f, ('{:<' + str(max_key_len) + 's} :: {}').format(k, get(k))

def load(path):
  with open(path) as load_f:
    for line in load_f:
      k, v = line.split(SEPARATOR)
      k = k.strip()
      v = v.strip()
      v = coerce_arg(v)
      dynamic(k, v)

#sys.modules[__name__] = Config(sys.modules)

def handle_flags():
  args = sys.argv[1:]
  args.reverse()
  while args:
    key = args.pop()
    if key[:2] != '--':
      logger.warn('ignoring flag %s', key)
      continue
    if not args or args[-1][:2] == '--':
      value = None
    else:
      value = args.pop()
    key = key[2:]
    value = coerce_arg(value)
    commandline(key, value)

def log_to_file(path):
  root_logger = logging.getLogger()
  file_log_handler = logging.FileHandler(path)
  file_log_handler.setFormatter(logging_utils.FileFormatter())
  root_logger.addHandler(file_log_handler)
