[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3df05a30a7234a19a7b74debc1a60658)](https://www.codacy.com/app/LincolnBryant/vc3-remote-manager?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=vc3-project/vc3-remote-manager&amp;utm_campaign=Badge_Grade)

Requirements:
 * `python-paramiko` package is installed
 * target is one of RedHat6, RedHat7, Ubuntu14, Ubuntu16, Debian6, Debian7
 * keybased auth is already setup between hosts
 * you can write to `/tmp/bosco`
 * you can mktemp dirs in `/tmp`

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
