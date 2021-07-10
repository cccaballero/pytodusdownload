from setuptools import setup

setup(
    name='pytodusdownload',
    version='0.1',
    packages=['pytodusdownload'],
    entry_points = {
            'console_scripts': ['pytodusdownload=pytodusdownload.pytodusdownload:main']
    },
    install_requires = [
        "requests == 2.25.1",
        "tqdm == 4.60.0",
        "todus == 0.1.0"
    ],
    url='https://github.com/cccaballero/pytodusdownload',
    license='AGPL',
    author='Carlos Cesar Caballero Díaz',
    description='Simple ToDus files downloader'
)
