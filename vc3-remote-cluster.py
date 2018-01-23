#!/usr/bin/env python

from __future__ import print_function

import argparse
import paramiko
import logging
import sys
import os

__version__ = "0.1.0" 

class RemoteCluster(object):
    """
    Remote cluster class.

    Controls SSH to a remote resource for BLAHP and Condor remote GAHP
    installation.
    """

    def __init__(self,
                    installdir=None,
                    remotehost=None,
                    user=None,
                    lrms=None,
                    loglevel=None
                ):
        self.installdir = installdir
        self.remotehost = remotehost
        self.user       = user
        self.lrms       = lrms
        self.loglevel   = loglevel
        # Setup logging
        self._setup_logging(self.loglevel)
        # setup Paramiko
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.remotehost,username=self.user)
            self.sftp = self.ssh.open_sftp()
        except Exception as e:
            self.log.debug(e)
            self.log.error("Failed to establish SSH connection")
            
    def install(self):
        """
        Externally-facing class for moving artifacts to the remote side
        """

        self._mkinstalldir()
            
    def status(self):
        """
        Check the status of currently configured clusters
        """
    
    def remove(self):
        """
        Remove currently configured clusters
        """

    def config_lrms_attributes(self):
        """
        Add the resource-specific and user-specific quirks necessary for a site.

        e.g. PBS or SLURM preprocessor config, HTCondor submit file requirements, etc
        """

    def cleanup(self):
        self.sftp.close()
        self.ssh.close()
        sys.exit(1)

    def _mkinstalldir(self):
        """
        Create the installation directory for the BLAHP and remote GAHP files
        """
        self.log.info("Creating installation directory %s" % self.installdir)
        # spaces are important
        (stdin,stdout,stderr) = self.ssh.exec_command("mkdir -p " + self.installdir)
        error = stderr.readlines()
        if error:
            self.log.error("Could not create installation dir")
            self.log.debug("".join(error).rstrip())
            self.cleanup()

    def _install_blahp(self):
        """
        Pull the BLAHP scripts from a local HTCondor install and then copy them
        over to the remote side
        """

    def _install_glite(self):
        """
        Pull the glite scripts from a local HTCondor install and then copy them
        over to the remote side
        """

    def _config_ftgahp(self):
        """
        This method will create the configuration for the condor file transfer
        GAHP binary that runs on the remote side. 

        previous config:

        cat >$remote_glite_dir/etc/condor_config.ft-gahp 2>/dev/null <<EOF
        BOSCO_SANDBOX_DIR=\$ENV(HOME)/$remote_sandbox_dir
        LOG=\$ENV(HOME)/$remote_base_dir_host/glite/log
        FT_GAHP_LOG=\$(LOG)/FTGahpLog
        SEC_CLIENT_AUTHENTICATION_METHODS = FS, PASSWORD
        SEC_PASSWORD_FILE = \$ENV(HOME)/$remote_base_dir_host/glite/etc/passwdfile
        USE_SHARED_PORT = False
        ENABLE_URL_TRANSFERS = False
        EOF
        """

    def _setup_logging(self, loglevel):
        """
        Setup the logging handler and format
        """
        formatstr = "[%(levelname)s] %(asctime)s %(module)s.%(funcName)s(): %(message)s"
        self.log = logging.getLogger()
        hdlr = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(formatstr)
        hdlr.setFormatter(formatter)
        self.log.addHandler(hdlr)
        self.log.setLevel(loglevel)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Install HTCondor Remote GAHP and BLAH")
    parser.add_argument("-v", "--verbosity", action="count", default=0)
    subparsers = parser.add_subparsers(title='subcommands',description='additional subcommands')

    parser_install = subparsers.add_parser('install', help='install help')
    parser_install.set_defaults(which='install')
    parser_install.add_argument("remotehost", help="Hostname of the remote batch submitter")
    parser_install.add_argument("lrms", action="store",
        help="Type of local resource management system. One of: condor, slurm, pbs, lsf")

    parser_install.add_argument("-i","--installdir", action="store",
        help="Installation path (default: $HOME/.condor/remote)", default="$HOME/.condor/remote")
    parser_install.add_argument("-u", "--user", action="store",
        help="Username on the remote submit host (default: $USER)", default=os.environ['USER'])

    args = parser.parse_args()

    if args.verbosity >= 2:
        print("[DEBUG] logging enabled")
        loglevel=10
    elif args.verbosity == 1:
        print("[INFO] logging enabled")
        loglevel=20
    else:
        loglevel=30

    if args.which == 'install':
        rc = RemoteCluster(
            installdir=args.installdir,
            remotehost=args.remotehost,
            user=args.user,
            lrms=args.lrms,
            loglevel=loglevel
        )
        rc.install()
