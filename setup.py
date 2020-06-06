import os
from setuptools import find_packages, setup

install_requires = [
    'Django>=2.0',
    'django-extensions>=2.0',
    'django-nested-admin>=3.2.4',
]

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-rateslide',
    version='0.9',
    packages=find_packages(),
    include_package_data=True,
    license='LGPL 2.1 License',
    description='A Django app to create questionnares and presentation including openslide.',
    long_description=README,
    url='https://github.com/JanOosting/django-rateslide',
    author='Jan Oosting',
    author_email='j.oosting@lumc.nl',
    install_requires=install_requires,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: LGPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
