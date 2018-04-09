from __future__ import print_function
from setuptools import setup
import os

# shamelessly stolen from stack overflow
def package_files(directory):
    paths = []
    for (path, _, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths

extra_files = package_files('patches')

setup(
    name="vc3-remote-manager",
    version="0.5.0",
    description="Tool for installing HTCondor remote GAHP and blahp",
    license='GPL',
    author='VC3 Team',
    author_email='vc3-project@googlegroups.com',
    long_description=open('README.md').read(),
    install_requires=['paramiko'],
    packages = ['vc3remotemanager'],
    package_data={'vc3remotemanager': extra_files},
    include_package_data=True,
    scripts = ['scripts/vc3-remote-manager'],
    )
