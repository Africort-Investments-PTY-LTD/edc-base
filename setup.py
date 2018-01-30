# -*- coding: utf-8 -*-
import os
from setuptools import setup
from setuptools import find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
setup(
    name='edc-base',
    version='0.2.18',
    author=u'Erik van Widenfelt',
    author_email='ew2789@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    url='http://github.com/botswana-harvard/edc-base',
    license='GPL licence, see LICENCE',
    description='Base mixins and utilities for botswana-harvard/edc projects.',
    long_description=README,
    zip_safe=False,
    keywords='django base models fields forms admin',
    install_requires=[
        'django',
        # 'django-simple-history',  until new release for DJ2.0
        'django-js-reverse',
        'django-logentry-admin',
        'django-debug-toolbar',
        'django-extensions',
        'python-dateutil',
        'docutils',
        'model_mommy',
        'Faker',
        'pytz',
        'arrow',
        'python-memcached',
        'django-tz-detect',  # can this be removed??
        'mysqlclient',
        'tqdm',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
