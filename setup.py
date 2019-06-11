from setuptools import setup

name = 'protex'

setup(
    name=name,
    version='1.0',
    description='Clean Latex sources without loosing track of positions',
    author='Théo (Lattay) Cavignac',
    author_email='theo.cavignac@gmail.com',
    packages=[name],
    long_description=open("README.md").read(),
    entry_points={
        'console_scripts': ['{0}={0}.__main__:App'.format(name)],
    }
)
