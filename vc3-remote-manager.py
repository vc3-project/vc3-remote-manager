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
import shlex
import sys
import tarfile
import tempfile
import textwrap

try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse


from vc3remotemanager.ssh import SSHManager
from vc3remotemanager.cluster import Cluster
from vc3remotemanager.bosco import Bosco

__version__ = "0.2.0"

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
        help="Sandbox directory (default: $installdir/bosco/sandbox)",
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
