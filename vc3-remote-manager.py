#!/usr/bin/python

from __future__ import print_function
from ftplib import FTP
from tarfile import TarFile


import argparse
import errno
import logging
import os
import paramiko
import re
import shutil
import sys
import tarfile
import tempfile
import textwrap

try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

__version__ = "0.2.0"

class SSHManager(object):
    def __init__(self, host, port, login):
        self.login = login
        self.port  = port
        self.host  = host

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname=self.host,port=self.port,username=self.login)
            self.sftp = self.client.open_sftp()
        except Exception as e:
            log.debug(e)
            log.error("Failed to establish SSH connection")
            sys.exit(1)

    def remote_cmd(self,cmd):
        """
        Wraps around exec_command for a bit nicer output
        """
        log.debug("Executing command %s" % cmd)
        (stdin,stdout,stderr) = self.client.exec_command(cmd)
        out = "".join(stdout.readlines()).rstrip()
        err = "".join(stderr.readlines()).rstrip()

        return out, err
        

    #def put(self, dst, *srcs, recurse=False):
    #    """
    #    Accept any number of src files, copy to destination
    #    """
    #    try: self.sftp.lstat(dst)
    #    except:
    #        self.log.debug("Cannot stat, assuming")

    #    files=[]
    #    dirs=[]
    #    for s in srcs:
    #        if os.path.isdir(s):
    #            for root, d, f in os.walk(s):
    #                for file in f:
    #                    files.append(os.path.join(root,file)) 
    #                for dir in d:
    #                    dirs.append(os.path.join(root,dir))


    def cleanup(self):
        """
        Close SSH, SFTP connnections
        """
        self.sftp.close()
        self.client.close()

class Bosco(object):
    def __init__(self, lrms, version, repository, tag, cachedir, installdir, sandbox):
        self.lrms       = lrms
        self.version    = version
        self.repository = repository
        self.tag        = tag
        self.cachedir   = cachedir

        try:
            self.installdir = cluster.resolve_path(installdir)
            log.debug("Installdir is %s" % self.installdir)
        except:
            log.warn("Couldn't resolve installdir.. things might not work")
            self.installdir = installdir

        if sandbox is None:
            self.sandbox = os.path.join(self.installdir,"sandbox")
            log.debug("Sandbox directory not specified, defaulting to %s" % self.sandbox)
        else:
            self.sandbox = sandbox
            log.debug("Sandbox directory is %s" % self.sandbox)

        self.etcdir = self.installdir + "/bosco/glite/etc"
        
    def cache_tarballs(self):
        r = urlparse(self.repository)
        path = r.path + "/" + self.version
        log.debug("repo is %s " % r.netloc)
        log.debug("path is %s " % path)

        ftp = FTP(r.netloc)
        ftp.login()
        ftp.cwd(path)
        files = ftp.nlst()
        match = "bosco-"
        tarballs = [s for s in files if re.match(match, s)] 

        dldir = os.path.join(self.cachedir, self.version)
   
        try:
            os.makedirs(dldir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
        
        # compare what we have on disk to upstream
        to_dl = set(tarballs) - set(os.listdir(dldir))

        if to_dl:
            log.info("Caching missing tarballs: %s" % ", ".join(to_dl))
            for tar in to_dl:
                fn = os.path.join(dldir, tar)
                with open(fn, 'wb') as f:
                    log.debug("Downloading.. %s" % tar)
                    ftp.retrbinary('RETR ' + tar, f.write) 
        else:
            log.debug("Nothing to download, continuing..")

        ftp.close()

    def extract_blahp(self, distro):
        """
        Extract the BLAHP shared libs and bins for the target platform and dump
        them to a temporary directory
        """
        tempdir = tempfile.mkdtemp()
        log.debug("Temporary working directory: %s" % tempdir)

        tarfile = os.path.join(self.cachedir,self.version,"bosco-1.2-x86_64_" + distro + ".tar.gz")
    
        cdir = 'condor-8.6.6-x86_64_RedHat6-stripped/'

        blahp_files = [
            'lib/libclassad.so.8.6.6', 
            'lib/libclassad.so.8',
            'lib/libclassad.so',
            'lib/libcondor_utils_8_6_6.so',
            'sbin/condor_ft-gahp' ]
        blahp_dirs = [
            'lib/condor/', 
            'libexec/glite/bin' ]

        # open the tarball, extract blahp_files and blahp_dirs to tmp
        with TarFile.open(tarfile) as t:
            members = []
            for file in blahp_files:
                members.append(t.getmember(os.path.join(cdir,file)))
            for dir in blahp_dirs:
                match = os.path.join(cdir, dir)
                files = [t.getmember(s) for s in t.getnames() if re.match(match, s)]
                members.extend(files)

            log.debug("Extracting %s to %s" % (members, tempdir))
            t.extractall(tempdir,members)

        # once things are in tmp, we need to need to move things around and
        # make some directories
        dirs = [ 'bosco/glite/etc', 
                 'bosco/glite/log', 
                 'bosco/sandbox' ]
        log.debug("Creating BOSCO directories...")
        for dir in dirs:
            os.makedirs(os.path.join(tempdir, dir))

        # list of files and directories that need to move from the extracted tarball to the bosco dir
        to_move = (
            ['lib','bosco/glite/lib'],
            ['libexec/glite/bin', 'bosco/glite/bin'],
            ['sbin/condor_ft-gahp', 'bosco/glite/bin/condor_ft-gahp'] )

        for tuple in to_move:
            src = os.path.join(tempdir,cdir,tuple[0])
            dst = os.path.join(tempdir,tuple[1])
            log.debug("Moving %s to %s" % (src,dst))
            shutil.move(src,dst)
            
        log.debug("Deleting old directory: %s " % cdir)
        shutil.rmtree(os.path.join(tempdir,cdir))

        return tempdir
    

    def create_tarball(self, dst, src):
        outfile = dst + ".tar.gz"
        with tarfile.open(outfile, "w:gz") as tar:
            tar.add(src, arcname=os.path.basename(src))
        return outfile


    def config_ft_gahp(self):
        #cat >$remote_glite_dir/etc/condor_config.ft-gahp 2>/dev/null <<EOF
        #BOSCO_SANDBOX_DIR=\$ENV(HOME)/$remote_sandbox_dir
        #LOG=\$ENV(HOME)/$remote_base_dir_host/glite/log
        #FT_GAHP_LOG=\$(LOG)/FTGahpLog
        #SEC_CLIENT_AUTHENTICATION_METHODS = FS, PASSWORD
        #SEC_PASSWORD_FILE = \$ENV(HOME)/$remote_base_dir_host/glite/etc/passwdfile
        #USE_SHARED_PORT = False
        #ENABLE_URL_TRANSFERS = False
        #EOF
        config = """\
            BOSCO_SANDBOX_DIR=%s
            LOG=%s/glite/log
            FT_GAHP_LOG=$(LOG)/FTGahpLog
            SEC_CLIENT_AUTHENTICATION_METHODS = FS, PASSWORD
            SEC_PASSWORD_FILE = %s/glite/etc/passwdfile
            USE_SHARED_PORT = False
            ENABLE_URL_TRANSFERS = False
        """ % (self.sandbox, self.installdir, self.installdir)

        c = textwrap.dedent(config)
        cfgfile = os.path.join(self.etcdir,"condor_config.ft-gahp")
        log.info("Writing HTCondor File Transfer GAHP config file %s" % cfgfile)
        with ssh.sftp.open(cfgfile, 'wb') as f:
            f.write(c)


class Cluster(object):
    def __init__(self):
        """
        This is a stub
        """

    def resolve_path(self,path):
        """
        Determine what $HOME or ~ is on the remote side
        """
        home, _ = ssh.remote_cmd("echo $HOME")
        log.debug("$HOME is %s" % home)

        if "~" or "$HOME" in path:
            tokens = path.split("/")[1::]
            out = os.path.join(home,'/'.join(tokens))
        else:
            out = path

        return out
        

    def resolve_platform(self):
        """
        Try to identify the remote platform. Currently RH+variants/Debian/Ubuntu
        are supported. A lot of code was lifted from the 'blivet' lib
        """
        #(stdin, stdout, stderr) = self.ssh.exec_command("uname -p")
        #arch = "".join(stdout.readlines()).rstrip()
        #self.log.debug("Remote architecture is: " + arch)
        #if "x86_64" not in arch:
        #    self.log.error("Only x86_64 architecture is supported")
        #    raise Exception

        search_path = ['/etc/os-release','/etc/redhat-release']
        for path in search_path:
            try:
                ssh.sftp.lstat(path)
                f = path
                break
            except IOError as e:
                f = None
                log.debug("Couldn't open %s, continuing.." % path)
        if f is None:
            log.error("Unknown or unsupported distribution")
            sys.exit(1)

        if 'os-release' in f:
            log.debug("Parsing os-release")
            with ssh.sftp.file(f) as fh:
                    parser = shlex.shlex(f)
                    while True:
                        key = parser.get_token()
                        if key == parser.eof:
                            break
                        elif key == "NAME":
                            # Throw away the "=".
                            parser.get_token()
                            relName = parser.get_token().strip("'\"")
                        elif key == "VERSION_ID":
                            # Throw away the "=".
                            parser.get_token()
                            relVer = parser.get_token().strip("'\"")
        elif 'redhat-release' in f:
            log.debug("Parsing redhat-release")
            with ssh.sftp.file(f) as fh:
                relstr = fh.readline().strip()
            (product, sep, version) = relstr.partition(" release ")
            if sep:
                relName = product
                relVer = version.split()[0].split(".",1)[0]

        log.info("Remote distribution and version is: %s %s" % (relName, relVer))

        # assume Linux for now
        if any(map(lambda(p): re.search(p,relName, re.I), ["red ?hat", "scientific", "centos"])):
            distro = "RedHat" + relVer
        elif relName in ["Debian"]:
            distro = "Debian" + relVer
        elif relName in ["Ubuntu"]:
            distro = "Ubuntu" + relVer

        return distro

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Install BLAHP and manage remote clusters")
    parser.add_argument("-v", "--verbose", action="store_true",
        help="Set logger to INFO")
    parser.add_argument("-d", "--debug", action="store_true",
        help="Set logger to DEBUG")
    
    parser.add_argument("host", action="store", 
        help="Hostname of the remote batch system")
    parser.add_argument("-p", "--port", action="store", 
        help="Port of the remote host (default: 22)", default=22)
    parser.add_argument("-l", "--login", action="store", 
        help="Login name of the user on the remote host (default: $USER)", 
        default=os.environ['USER'])

    parser.add_argument("-r", "--repository", action="store", 
        help="BOSCO repository location (default: ftp://ftp.cs.wisc.edu/condor/bosco)",
        default="ftp://ftp.cs.wisc.edu/condor/bosco")
    parser.add_argument("-b", "--bosco-version", action="store", 
        help="BOSCO version (default 1.2.10)",
        default="1.2.10")
    parser.add_argument("-c", "--cachedir", action="store", 
        help="local BOSCO tarball cache dir (default: /tmp/bosco)",
        default="/tmp/bosco")
    parser.add_argument("-i", "--installdir", action="store", 
        help="Remote installation directory (default: ~/.condor)",
        default="~/.condor")
    parser.add_argument("-t", "--tag", action="store", 
        help="Request tag hook (default: None)",
        default=None)
    parser.add_argument("-s", "--sandbox", action="store", 
        help="Sandbox directory (default: %installdir/sandbox)",
        default=None)

    args = parser.parse_args()

    if args.debug == True:
        print("[DEBUG] logging enabled")
        loglevel=10
    elif args.verbose == True:
        print("[INFO] logging enabled")
        loglevel=20
    else:
        loglevel=30

    formatstr = "[%(levelname)s] %(asctime)s %(module)s.%(funcName)s(): %(message)s"
    log = logging.getLogger()
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(formatstr)
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(loglevel)

    ### the magic happens here ###

    """
    Initialize SSHManager and Cluster classes.
    """
    ssh = SSHManager(args.host, args.port, args.login)
    cluster = Cluster()

    """ 
    Download platform tarballs, extract bosco components, and transfer them
    to the remote side
    """

    log.info("Retrieving BOSCO files...")
    b = Bosco("condor", args.bosco_version, args.repository, args.tag, args.cachedir, args.installdir, args.sandbox)
    b.cache_tarballs()
    distro = cluster.resolve_platform()
    log.info("Extracting BOSCO files for platform %s" % distro)
    bdir = b.extract_blahp(distro)
    if args.tag is not None:
        tarname = "bosco" + "-" + args.tag
    else:
        tarname = "bosco"
    log.info("Creating new BOSCO tarball for target %s" % args.host)
    t = b.create_tarball(tarname, os.path.join(bdir,"bosco"))

    src = os.path.join(os.getcwd(),t)
    dst = cluster.resolve_path(args.installdir + "/" + t)
    log.info("Transferring %s to %s" % (src, dst))
    try:
        ssh.sftp.mkdir(cluster.resolve_path(args.installdir))
    except IOError as e:
        log.debug("Couldn't create installdir.. perhaps it already exists?")
    try: 
        ssh.sftp.put(src, dst)
    except Exception as e:
        log.error("Couldn't transfer %s to %s!" % (src, args.host + ":" + dst))
        log.debug(e)
        sys.exit(1)

    log.info("Extracting %s to %s" % ((args.host + ":" + dst),args.installdir))
    out, err = ssh.remote_cmd("tar -xzf " + dst + " -C " + args.installdir )
    if err is not '':
        log.debug(err)
    log.info("Deleting temporary file %s" % dst)
    ssh.sftp.remove(dst)

    """ 
    Add configuration for the site
    """
    b.config_ft_gahp()

    """
    Close any remaining connections and clean up any temporary files
    """
    log.info("Terminating SSH connections...")
    ssh.cleanup()
    log.info("Deleting temporary file %s" % bdir)
    shutil.rmtree(bdir)
