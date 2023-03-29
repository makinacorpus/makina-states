#!/usr/bin/env python3
# generate python tags to be imported from inside and  outside the VM (from the hosts)
# main utility is to generate vim tags afterwards importing the .env in the shell
import os, sys, re
CWD = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
path = 'mc_states/saltcaller.py'
sc = open(path).read()
content = open('ansible/library/saltcall.py.in').read()
sanitizer = re.compile('^#.*', flags=re.M)
import base64
sc = base64.b64encode(sanitizer.sub('', sc).encode()).decode()
content = content.replace(
    'SALTCALLER = """',
    'SALTCALLER = """\n{0}'.format(sc))
with open('ansible/library/saltcall.py', 'w') as d:
    d.write(content)
    os.chmod(path, 0o755)
