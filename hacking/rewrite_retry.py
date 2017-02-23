#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import subprocess
p = subprocess.check_output('grep pkgrepo.managed $(grep /srv/makina-states/salt/makina-states locfiles)|sed -re "s/:.*//g"|sort -u', shell=True)
for f in p.splitlines():
    f = f.strip()
    if f:
        with open(f) as fic:
            content = fic.read()
        lcontent = content.splitlines()
        ncontent = []
        for l in lcontent:
            ncontent.append(l)
            if 'pkgrepo.managed' in l:
                ncontent.append('    - retry: {attempts: 6, interval: 10}')
        if ncontent != lcontent:
            with open(f, 'w') as fic:
                fic.write("\n".join(ncontent)+"\n")
# vim:set et sts=4 ts=4 tw=80:
