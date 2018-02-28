from ftplib import FTP
from tarfile import TarFile

import errno
import logging
import os
import re
import shutil
import tarfile
import tempfile
import textwrap

try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

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
            self.sandbox = os.path.join(self.installdir,"bosco/sandbox")
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

        cdir = 'condor-8.6.6-x86_64_' + distro + '-stripped/'

        blahp_files = [
            'lib/libclassad.so.8.6.6',
            'lib/libclassad.so.8',
            'lib/libclassad.so',
            'lib/libcondor_utils_8_6_6.so',
            'sbin/condor_ft-gahp' ]
        blahp_dirs = [
            'lib/condor/',
            'libexec/glite/bin',
            'libexec/glite/etc' ]

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
        dirs = [ 'bosco/glite/log', 'bosco/sandbox' ]
        log.debug("Creating BOSCO directories...")
        for dir in dirs:
            os.makedirs(os.path.join(tempdir, dir))

        # list of files and directories that need to move from the extracted tarball to the bosco dir
        to_move = (
            ['lib','bosco/glite/lib'],
            ['libexec/glite/bin', 'bosco/glite/bin'],
            ['libexec/glite/etc', 'bosco/glite/etc'],
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
            LOG=%s/bosco/glite/log
            FT_GAHP_LOG=$(LOG)/FTGahpLog
            SEC_CLIENT_AUTHENTICATION_METHODS = FS, PASSWORD
            SEC_PASSWORD_FILE = %s/bosco/glite/etc/passwdfile
            USE_SHARED_PORT = False
            ENABLE_URL_TRANSFERS = False
        """ % (self.sandbox, self.installdir, self.installdir)

        c = textwrap.dedent(config)
        cfgfile = os.path.join(self.etcdir,"condor_config.ft-gahp")
        log.info("Writing HTCondor File Transfer GAHP config file %s" % cfgfile)
        with ssh.sftp.open(cfgfile, 'wb') as f:
            f.write(c)

