from setuptools import setup, find_packages
import os

version = '0.4.1'

setup(name='monet.calendar.portlet',
      version=version,
      description="Calendar related portlets for the Plone Monet Calendar events suite",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        ],
      keywords='plone plonegov calendar event monet',
      author='RedTurtle Technology',
      author_email='sviluppoplone@redturtle.it',
      url='http://plone.org/products/monet.calendar.star',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['monet', 'monet.calendar'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'monet.calendar.event',
          'monet.calendar.extensions>=0.9.0',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
