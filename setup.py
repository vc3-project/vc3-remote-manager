from distutils.core import setup

setup(
    name="vc3-remote-manager",
    version="0.3.0",
    description="Tool for installing HTCondor remote GAHP and blahp",
    license='GPL',
    author='VC3 Team',
    author_email='vc3-project@googlegroups.com',
    long_description=open('README.md').read(),
    install_requires=['paramiko'],
    packages = ['vc3remotemanager'],
    scripts = ['scripts/vc3-remote-manager.py'],
    )
