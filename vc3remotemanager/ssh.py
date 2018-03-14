import logging
import paramiko
import sys

class SSHManager(object):
    def __init__(self, host, port, login):
        self.login = login
        self.port  = port
        self.host  = host
        self.log   = logging.getLogger(__name__)

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname=self.host,port=self.port,username=self.login)
            self.sftp = self.client.open_sftp()
        except Exception as e:
            self.log.debug(e)
            self.log.error("Failed to establish SSH connection")
            sys.exit(1)

    def remote_cmd(self,cmd):
        """
        Wraps around exec_command for a bit nicer output
        """
        self.log.debug("Executing command %s" % cmd)
        (_,stdout,stderr) = self.client.exec_command(cmd)
        out = "".join(stdout.readlines()).rstrip()
        err = "".join(stderr.readlines()).rstrip()

        return out, err

    def cleanup(self):
        """
        Close SSH, SFTP connnections
        """
        self.sftp.close()
        self.client.close()
