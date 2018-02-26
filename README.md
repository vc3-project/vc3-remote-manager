Requirements:
    - `python-paramiko` package is installed
    -  target is one of RedHat6, RedHat7, Ubuntu14, Ubuntu16, Debian6, Debian7
    -  keybased auth is already setup between hosts
    -  you can write to `/tmp/bosco`
    -  you can mktemp dirs in `/tmp`
    -  a `condor_schedd` is running on the local side


Sample invocation:
    ```
    ./vc3-remote-manager.py login03.osgconnect.net --installdir . -v
    ```

will install to `~/bosco` on the remote side, and configure `~/bosco/etc/condor_ft-gahp.config` appropriately.

You can then submit test jobs like so:

```
universe = grid
executable = /bin/whoami
transfer_executable = true
grid_resource = batch condor login03.osgconnect.net --rgahp-glite /home/lincolnb/bosco/glite --rgahp-nokey
output = $(Cluster).$(Process).out
error = $(Cluster).$(Process).err
log = $(Cluster).log
queue
```
