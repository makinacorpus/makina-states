#!/usr/bin/env python
# generate python tags to be imported from inside and  outside the VM (from the hosts)
# main utility is to generate vim tags afterwards importing the .env in the shell
import os, sys
CWD = os.path.dirname(os.path.abspath('$(dirname $0)'))
path = 'mc_states/saltcaller.py'
sc = open(path).read()
content = open('ansible/library/saltcall.py.in').read()
content = content.replace(
    'SALTCALLER = """',
    'SALTCALLER = """\n{0}'.format(sc))
with open('ansible/library/saltcall.py', 'w') as d:
    d.write(content)
    os.chmod(path, 0o755)
