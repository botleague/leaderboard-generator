import os
from os.path import abspath, dirname, join
from typing import List

from setuptools import setup


def get_requires() -> List[str]:
    with open('requirements.txt') as reqs_file:
        reqs = reqs_file.read().split(os.sep)
    return reqs


# Read the README markdown data from README.md
with open(abspath(join(dirname(__file__), 'README.md')), 'rb') as readme_file:
    __readme__ = readme_file.read().decode('utf-8')

setup(
    name='leaderboard-generator',
    version='0.0.1',
    description='Generates Bot League leaderboard',
    long_description=__readme__,
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Environment :: Console'
    ],
    keywords='botleague deepdrive',
    url='http://github.com/deepdrive/botleauge',
    author='Craig Quiter',
    author_email='craig@deepdrive.io',
    license='MIT',
    packages=['leaderboard_generator'],
    zip_safe=True,
    python_requires='>=3.6',
    install_requires=get_requires()
)
