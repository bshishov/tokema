from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='tokema',
    version='0.0.2',
    description='Token matching parser',
    url='https://github.com/bshishov/tokema',
    author='Boris Shishov',
    author_email='borisshishov@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['tokema'],
    package_dir={'': 'src'},
    license="MIT",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries'
    ],
    python_requires='>=3.6'
)
