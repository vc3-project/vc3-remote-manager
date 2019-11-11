import logging
import os
import subprocess
import distutils.spawn
import pexpect
import tempfile
import shlex
from sshbase import SSHBase

class GSISSHManager(SSHBase):
    """
    GSISSH Manager
    """
    def __init__(self, **kwargs):
        super(GSISSHManager, self).__init__(**kwargs)
        self.x509proxy = kwargs.get('x509proxy', None)
        self.env = os.environ
        self.env['X509_USER_PROXY'] = self.x509proxy

        try:
            self.gsissh  = distutils.spawn.find_executable("gsissh")

            if not self.gsissh:
                raise IOError("Could not find gsissh binary.")
        except FileNotFoundError as e:
            self.log.debug(e)
            raise
        
        self.sftp = GSISFTPClient(self.login, self.host, self.x509proxy, self.port)

    def remote_cmd(self, cmd):
        """
        Execute GSISSH command via suprocess
        """
        args  = [self.gsissh]
        args += ['-q']
        args += ['-o']
        args += ['StrictHostKeyChecking=no']
        args += ['-p']
        args += [str(self.port)]
        args += ['{user}@{host}'.format(user=self.login, host=self.host)]
        args += shlex.split(cmd)
        
        p = subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        out = out.rstrip()
        err = err.rstrip()

        return out, err

    def cleanup(self):
        """
        Cleanup connections.
        """
        self.sftp.cleanup()

class GSISFTPClient(object):
    """
    GSISFTP client
    """
    def __init__(self, username, host, x509proxy, port = 22):
        self.username = username
        self.host = host
        self.port = port
        self.x509proxy = x509proxy
        self.prompt = 'sftp>'
        self.fileobject = GSISFTPFileObject
        self.log = logging.getLogger(__name__)

        try:
            self.gsisftp  = distutils.spawn.find_executable("gsisftp")
            if not self.gsisftp:
                raise IOError("Could not find gsisftp binary.")

            self.session = pexpect.spawn('env X509_USER_PROXY={x509proxy} '
                                         '{gsisftp} -P {port} {user}@{host}'
                                         .format(x509proxy=self.x509proxy, gsisftp=self.gsisftp,
                                                 port=self.port, user=self.username, host=self.host)
                                        )
            self.session.expect(self.prompt)
        except Exception as e:
            self.log.debug(e)
            raise

    def mkdir(self, dirpath):
        """
        Create a remote directory
        """
        try:
            self.session.sendline('mkdir %s' % dirpath)
            self.session.expect(self.prompt)
            res = self.session.before
            if "Couldn\'t create directory" in res:
                raise IOError("Could not create directory.")
        except IOError as e:
            self.log.debug(e)
            raise

        return res

    def lstat(self, filepath):
        """
        stat a remote file
        """
        try:
            self.session.sendline('ls -l %s' % filepath)
            self.session.expect(self.prompt)
            res = self.session.before
            if "No such file or directory" in res or "not found" in res:
                raise IOError("Could not stat file.")

            res = res.strip().split('\n')[1:]
        except IOError as e:
            self.log.debug(e)
            raise

        return res

    def put(self, lfpath, rfpath):
        """
        put local file to remote file
        """
        try:
            self.session.sendline('put -P %s %s' % (lfpath, rfpath))
            self.session.expect(self.prompt)
            res = self.session.before
            if "No such file or directory" in res or "is not a regular file" in res:
                raise IOError("Could not put file")
        except IOError:
            self.log.debug(res)
            raise

        return res

    def remove(self, rfpath):
        """
        Remote remote file
        """
        try:
            self.session.sendline('rm %s' % (rfpath))
            self.session.expect(self.prompt)
            res = self.session.before
            if "No such file or directory" in res or "not found" in res:
                raise IOError("Could not delete file")

        except IOError:
            self.log.debug(res)
            raise

        return res

    def get(self, rfpath, lfpath): 
        """
        Get remote file to local file
        """
        try:
            self.session.sendline('get -P %s %s' % (rfpath, lfpath))
            self.session.expect(self.prompt)
            res = self.session.before
            if "No such file or directory" in res or "not found" in res:
                raise IOError("Could not put file")

        except IOError:
            self.log.debug(res)
            raise

        return res

    def open(self, rfpath, mode='r'):
        """
        Open GSIFTP file object
        """
        # Create local temporary file, which
        # will be deleted when object is garbage collected.
        lfile = tempfile.NamedTemporaryFile()

        if 'r' in mode:
            self.get(rfpath, lfile.name)

        return self.fileobject(self, lfile.name, rfpath, mode)

    def file(self, rfpath, mode):
        return open(rfpath, mode)

    def cleanup(self):
        """
        Close SFTP connnection
        """
        self.session.close()


class GSISFTPFileObject(object):
    """
    GSISFTP file object
    """
    def __init__(self, gsisftpclient, lfpath, rfpath, mode='r'):
        self.lfpath  = lfpath
        self.lfile   = open(self.lfpath, mode)
        self.rfpath  = rfpath
        self.gsisftp = gsisftpclient
        self.mode    = mode
        self.log = logging.getLogger(__name__)

    def write(self, line):
        try:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(line)
            tfile.close()
            if 'w' in self.mode:
                self.gsisftp.put(tfile.name, self.rfpath)
                os.unlink(tfile.name)
            elif 'a' in self.mode:
                raise NotImplementedError("append mode is not implemented")
            else:
                raise IOError("File not open for writing. Use e.g.: wb mode")

        except IOError as e:
            self.log.debug(e)
            raise

    def readline(self):
        return self.lfile.readline()

    def readlines(self):
        return self.lfile.readlines()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.lfile.close()
