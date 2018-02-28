
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
        are supported. A lot of code was lifted from the 'blivet' lib which
        implicitly GPL-ifies this
        """
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
                    parser = shlex.shlex(fh)
                    while True:
                        key = parser.get_token()
                        if key == parser.eof:
                            break
                        elif key == "NAME":
                            # Throw away the "=".
                            parser.get_token()
                            relName = parser.get_token().strip("'\"")
                            log.debug(relName)
                        elif key == "VERSION_ID":
                            # Throw away the "=".
                            parser.get_token()
                            version = parser.get_token().strip("'\"")
                            relVer = version.split()[0].split(".",1)[0]
                            log.debug(relVer)

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
