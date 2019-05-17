import logging
import sys
import getpass

class SSHBase(object):
    def __init__(self, **kwargs):
        self.login          = kwargs.get('login', getpass.getuser())
        self.port           = kwargs.get('port', '22')
        self.host           = kwargs.get('host', None)
        self.log            = logging.getLogger(__name__)

    def remote_cmd(self,cmd):
        """
        Wraps around exec_command for a bit nicer output
        """
        pass

    def cleanup(self):
        """
        Close SSH, SFTP connnections
        """
        pass
