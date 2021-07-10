from setuptools import setup

setup(
    name='pytodusdownload',
    version='0.1',
    packages=['pytodusdownload'],
    entry_points = {
            'console_scripts': ['pytodusdownload=pytodusdownload.pytodusdownload:main']
    },
    url='https://github.com/cccaballero/pytodusdownload',
    license='AGPL',
    author='Carlos Cesar Caballero Díaz',
    description='Simple ToDus files downloader'
)
