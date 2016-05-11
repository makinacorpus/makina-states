#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import traceback
from setuptools import setup, find_packages

try:
    import pip
    HAS_PIP = True
except:
    HAS_PIP = False

version = {}
execfile("mc_states/version.py", version)


def read(*rnames):
    return open(
        os.path.join(".", *rnames)
    ).read()
READMES = [a
           for a in ['README', 'README.rst',
                     'README.md', 'README.txt']
           if os.path.exists(a)]
long_description = "\n\n".join(READMES)
classifiers = [
    "Programming Language :: Python",
    "Topic :: Software Development"]

name = 'mc_states'
version = version['VERSION']
src_dir = '.'
install_requires = ["setuptools"]
extra_requires = {}
candidates = {}
reqs_files_re = re.compile('.*requirements?(\\.(txt|pip))?',
                           re.S | re.I | re.U)
entry_points = {
    # z3c.autoinclude.plugin": ["target = plone"],
    # console_script": ["myscript = mysite:main"],
}
if HAS_PIP:
    reqs_files = []
    for req_folder in ['.', 'requirements', 'reqs', 'pip']:
        if os.path.exists(req_folder):
            for freq in os.listdir(req_folder):
                req = os.path.join(req_folder, freq)
                if (
                    reqs_files_re.match(freq) and
                    not req.endswith('.in') and
                    req not in reqs_files
                ):
                    reqs_files.append(req)
    for reqs_file in reqs_files:
        if os.path.isfile(reqs_file):
            reqs = []
            try:
                try:
                    reqs = [a.req for a in pip.req.parse_requirements(reqs_file)]
                except TypeError:
                    from pip.download import PipSession
                    reqs = [a.req for a in pip.req.parse_requirements(
                        reqs_file, session=PipSession())]
            except (Exception,) as exc:
                sys.stderr.write(traceback.format_exc())
                sys.stderr.write("\n")
                sys.stderr.write(
                    '{0} unreadable, getting next req file'.format(reqs_file))
                sys.stderr.write("\n")
                continue
            if not reqs:
                continue
            for req in reqs:
                pkgreq = "{0}".format(req.__class__)
                # match pip._vendor.pkg_resources.Requirement
                # match pkg_resources.Requirement
                if ".Requirement" not in pkgreq:
                    sys.stderr.write('{0} is not a req\n'.format(req))
		try:
                    name = req.project_name
                except AttributeError:
                    name = req.name
                if name not in candidates:
                    candidates[name] = "{0}".format(req)
                else:
                    raise ValueError(
                        '{1}: conflict for {0}'.format(req, reqs_file))
for c in [a for a in candidates]:
    val = candidates[c]
    if val not in install_requires:
        install_requires.append(val)
setup(name=name,
      version=version,
      namespace_packages=[],
      description=name,
      long_description=long_description,
      classifiers=classifiers,
      keywords="",
      author="foo",
      author_email="foo@foo.com",
      url="http://www.makina-corpus.com",
      license="GPL",
      packages=find_packages(src_dir),
      package_dir={"": src_dir},
      include_package_data=True,
      install_requires=install_requires,
      extras_require=extra_requires,
      entry_points=entry_points)
# vim:set ft=python:
