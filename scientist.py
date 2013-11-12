import config
import fridge
import logging
import os
import sys
import traceback

logger = logging.getLogger(__name__)

config.default('root', os.getcwd())
config.default('experiments_dir_name', 'work')
config.default('experiments_dir', os.path.join(config.root, config.experiments_dir_name))
config.default('work_dir', config.timestamp_dir(config.experiments_dir))
config.default('latest_link_file_name', 'latest')
config.default('latest_link_file', os.path.join(config.root, 'latest'))
config.default('failure_file_name', 'FAIL.txt')
config.default('failure_file', os.path.join(config.work_dir, config.failure_file_name))
config.default('config_file_name', 'config.txt')
config.default('config_file', os.path.join(config.work_dir, config.config_file_name))
config.default('log_file_name', 'run.log')
config.default('log_file', os.path.join(config.work_dir, config.log_file_name))
config.default('data_dir_name', 'data')
config.default('data_dir', os.path.join(config.root, config.data_dir_name))

config.default('pbs_ssh_promiscuous', True)

DEV = 'dev'
TEST = 'test'

class Experiment(object):

  # SETUP

  def __init__(self):
    self.__is_ready = False
    self.__stages = []
    config.handle_flags()

  def stage(self, fn):
    assert not self.__is_ready
    self.__stages.append(fn)

  def ready(self):
    assert not self.__is_ready
    self.__is_ready = True

  # EXECUTION

  def auto_resume(self):
    def ar_inner():
      with open(config.failure_file, 'w') as failure_f:
        config.dump(config.config_file)
        print >>failure_f, config.stage
    self.stage(ar_inner)

  def run_pbs(self):
    import pbs_utils
    import paramiko

    tarball_name = '%s_%s' % (self.__class__.__name__, config.timestamp())

    pbs_body = """
#!/bin/sh

#PBS -N %s
#PBS -M jda@cs.berkeley.edu
#PBS -q psi
#PBS -e localhost:/dev/null
#PBS -o localhost:/dev/null

cd $PBS_O_WORKDIR
exec &> pbs.log
. %s/bin/activate
./run.py --pbs False
""" % (tarball_name, config.pbs_virtualenv)

    with open('pbs.sh', 'w') as pbs_f:
      print >>pbs_f, pbs_body

    tarball_dest = os.path.join(config.root, '..', '%s.tar.gz' % tarball_name)
    pbs_utils.make_tarball(config.root, 
                           tarball_dest, ignore=[config.experiments_dir_name,
                                                 config.latest_link_file_name])

    ssh = paramiko.SSHClient()
    if config.pbs_ssh_promiscuous:
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(config.pbs_host, username=config.pbs_user)
    sftp = ssh.open_sftp()

    remote_tarball_dest = os.path.join(config.pbs_work_dir, '%s.tar.gz' % tarball_name)
    remote_root = os.path.join(config.pbs_work_dir, tarball_name)
    sftp.put(tarball_dest, remote_tarball_dest)

    commands = ['cd %s' % config.pbs_work_dir,
                'tar xzf %s' % remote_tarball_dest,
                'cd %s' % remote_root,
                'qsub pbs.sh']
    ssh.exec_command('; '.join(commands))

    #for line in stderr:
    #  logger.warn(line)
    #for line in stdout:
    #  logger.info(line)

  def run(self):

    if config.has('pbs') and config.pbs:
      self.run_pbs()
      return

    #if config.has('resume'):
    if os.path.exists(os.path.join(config.latest_link_file,
                                   config.failure_file_name)):
      print >>sys.stderr, 'Resume previous run? [Yn]'
      response = None
      while response not in ('y', 'n', ''):
        response = sys.stdin.readline().strip().lower()
      if response in ('y', ''):
        self.run_resume()
        return

    self.run_new()

  def run_new(self):
    # prevent accidental early start
    assert self.__is_ready

    # make some space to work in, and a pointer to it
    os.makedirs(config.work_dir)
    try:
      os.remove(config.latest_link_file)
    except OSError:
      pass
    os.symlink(config.work_dir, config.latest_link_file)

    config.dynamic('stage', 0)
    self.run_stages()

  def run_resume(self):
    config.load(os.path.join(config.latest_link_file, config.config_file_name))
    fridge.get_all_from_disk(config.work_dir)

    with open(config.failure_file) as failure_f:
      last_stage = int(failure_f.readline())
    config.dynamic('stage', last_stage)

    self.run_stages()

  def run_stages(self):

    config.log_to_file(config.log_file)
    logger.info('BEGIN')

    while config.stage < len(self.__stages):
      stage = self.__stages[config.stage]
      try:
        logger.info('running {.__name__}'.format(stage))
        stage()
      except:
        logger.error('error---saving state')
        with open(config.failure_file, 'w') as failure_f:
          print >>failure_f, config.stage
        #logger.error(traceback.format_exc())
        config.dump(config.config_file)
        raise

      config.dynamic('stage', config.stage + 1)
