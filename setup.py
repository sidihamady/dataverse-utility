from setuptools import setup
import os
import sys

if sys.version_info[0] < 3:
    with open('README.rst') as f:
        long_description = f.read()
    #
else:
    with open('README.rst', encoding='utf-8') as f:
        long_description = f.read()
    #
#

setup(
    name='DataverseUtility',
    version='1.0',
    description='Dataverse Utility',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Pr. Sidi Hamady',
    url='https://gitlab.univ-lorraine.fr/hamady/dataverse-utility',
    install_requires=['requests', 'tkinter'],
    download_url='https://gitlab.univ-lorraine.fr/hamady/dataverse-utility.git',
    py_modules=["DataverseUtility"],
    data_files=[
        ('.', ['iconmain.png']),
    ],
    include_package_data=True,
    package_dir={'':'.'},
)
