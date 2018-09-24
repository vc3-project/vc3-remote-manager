[![Codacy Badge](https://api.codacy.com/project/badge/Grade/bc14b84f503946f8a9d352af14f23631)](https://app.codacy.com/app/LincolnBryant/vc3-remote-manager?utm_source=github.com&utm_medium=referral&utm_content=vc3-project/vc3-remote-manager&utm_campaign=badger)

VC3 Remote Manager
===================
VC3 Remote Manager is a tool for installing HTCondor BLAHP to a remote system for BOSCO-like (see [1]) operation. 

Requirements
-------------
 * `python-paramiko` package is installed
 * target is one of RedHat6, RedHat7, Ubuntu14, Ubuntu16, Debian6, Debian7
 * keybased auth is already setup between hosts
 * you can write to `/tmp/bosco`
 * you can mktemp dirs in `/tmp`

Usage
-----
```bash
usage: vc3-remote-manager [-h] [-v] [-d] [-p PORT] [-l LOGIN]
                          [--gateway GATEWAY] [--gateway-port GATEWAY_PORT]
                          [--gateway-login GATEWAY_LOGIN]
                          [--gateway-key GATEWAY_KEY] [-r REPOSITORY]
                          [-b BOSCO_VERSION] [-c CACHEDIR] [-i INSTALLDIR]
                          [-t TAG] [-s SANDBOX] [-P PATCHSET]
                          [-R REMOTE_DISTRO] [-L CLUSTERLIST]
                          [-k PRIVATE_KEY_FILE]
                          host lrms

Install BLAHP and manage remote clusters

positional arguments:
  host                  Hostname of the remote batch system
  lrms                  Remote batch system to configure

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Set logger to INFO
  -d, --debug           Set logger to DEBUG
  -p PORT, --port PORT  Port of the remote host (default: 22)
  -l LOGIN, --login LOGIN
                        Login name of the user on the remote host (default:
                        $USER)
  --gateway GATEWAY     Hostname of the remote gateway host
  --gateway-port GATEWAY_PORT
                        Port of the remote gateway host (default: 22)
  --gateway-login GATEWAY_LOGIN
                        Login name of the user on the remote host (default:
                        $USER)
  --gateway-key GATEWAY_KEY
                        Private key for the remote gateway host (default:
                        autoconfigured)
  -r REPOSITORY, --repository REPOSITORY
                        BOSCO repository location (default:
                        ftp://ftp.cs.wisc.edu/condor/bosco)
  -b BOSCO_VERSION, --bosco-version BOSCO_VERSION
                        BOSCO version (default 1.2.10)
  -c CACHEDIR, --cachedir CACHEDIR
                        local BOSCO tarball cache dir (default: /tmp/bosco)
  -i INSTALLDIR, --installdir INSTALLDIR
                        Remote installation directory (default: ~/.condor)
  -t TAG, --tag TAG     Request tag hook (default: None)
  -s SANDBOX, --sandbox SANDBOX
                        Sandbox directory (default: $installdir/bosco/sandbox)
  -P PATCHSET, --patchset PATCHSET
                        Resource-specific patchset
  -R REMOTE_DISTRO, --remote-distro REMOTE_DISTRO
                        Remote distro override (default: autoconfigured)
  -L CLUSTERLIST, --clusterlist CLUSTERLIST
                        location of the cluster list file (default:
                        $cachedir/.clusterlist)
  -k PRIVATE_KEY_FILE, --private-key-file PRIVATE_KEY_FILE
                        location of private key file (default: autoconfigured)
```

Sample invocation:
```bash
python setup.py --user
./scripts/vc3-remote-manager.py login03.osgconnect.net condor -v
```

will install to `~/.condor/bosco` on the remote side, and configure `~/.condor/bosco/etc/condor_ft-gahp.config` appropriately.

You can then submit test jobs like so:

```
universe = grid
executable = /bin/whoami
transfer_executable = false
grid_resource = batch condor login03.osgconnect.net --rgahp-glite /home/lincolnb/.condor/bosco/glite --rgahp-nokey
output = $(Cluster).$(Process).out
error = $(Cluster).$(Process).err
log = $(Cluster).log
queue
```

References
------------
[1] https://research.cs.wisc.edu/htcondor/HTCondorWeek2013/presentations/WeitzelD_BOSCO.pdf
