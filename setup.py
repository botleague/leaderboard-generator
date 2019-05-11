from os.path import abspath, dirname, join
from setuptools import setup

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
    install_requires=[
        'setuptools>=38.6.0',
        'twine>=1.11.0',
        'wheel>=0.31.0',
        'requests',
        'Jinja2==2.10.1',
        'future==0.17.1',
        'watchdog==0.9.0',
        'PyGithub==1.43.6',
        'GitPython==2.1.11',
        'firebase-admin==2.16.0',
        'google-cloud-firestore==0.32.1',
        'google-cloud-storage==1.15.0',
        'cryptography==2.6.1',
        'pytest==4.4.1'
    ]
)
