import logging
from termcolor import colored

class PrettyFormatter(logging.Formatter):

  def format(self, record):
    namepart = '{.name:20}\t'.format(record)

    color = {
      logging.DEBUG:    'white',
      logging.INFO:     'blue',
      logging.WARN:     'yellow',
      logging.ERROR:    'red',
      logging.CRITICAL: 'magenta'
    }[record.levelno]
    levelpart = colored('{.levelname:8}'.format(record), color)

    msgpart = record.getMessage()
    return namepart + levelpart + msgpart

#                    format='%(name)-20s %(levelname)-8s %(message)s')

class FileFormatter(logging.Formatter):
  
  def format(self, record):
    return '%s :: %s :: %s' % (record.name, record.levelname,
        record.getMessage())
