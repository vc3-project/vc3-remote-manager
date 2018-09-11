import logging
import paramiko
import sys
import getpass

class SSHManager(object):
    def __init__(self, **kwargs):
        self.login          = kwargs.get('login', getpass.getuser())
        self.port           = kwargs.get('port', '22')
        self.host           = kwargs.get('host', None)
        self.privatekeyfile = kwargs.get('keyfile', None) # paramiko defaults to the usual places
        self.parent         = kwargs.get('parent', None) # Get parent object for nested ssh
        self.log            = logging.getLogger(__name__)

        if self.privatekeyfile is not None:
            try:
                self.log.debug("Private key file is %s" % self.privatekeyfile)
                k = paramiko.RSAKey.from_private_key_file(self.privatekeyfile)
            except PasswordRequiredException as e:
                self.log.info("Private key not in expected format... aborting")
                self.log.debug(e)
            except IOError as e:
                self.log.info("Cannot open private key file.. aborting")
                self.log.debug(e)
                raise
        else:
            k = None

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.parent is not None:
                # Nesting logic here. 
                pclient = self.parent.client
                self.log.debug("Opened parent SSHManager object %s", pclient)
                pclient.set_missing_host_key_policy('paramiko.AutoAddPolicy()')
                ptransport = pclient.get_transport()
                self.log.info("Opening nested connection from %s to %s", self.parent.host, self.host)
                localaddr = (self.parent.host, self.parent.port)
                destaddr = (self.host, self.port)
                pchannel = ptransport.open_channel("direct-tcpip", destaddr, localaddr)
                self.client.connect(hostname=self.host,port=int(self.port),username=self.login,pkey=k,sock=pchannel)
                self.sftp = self.client.open_sftp()
            else:
                self.client.connect(hostname=self.host,port=int(self.port),username=self.login,pkey=k)
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
