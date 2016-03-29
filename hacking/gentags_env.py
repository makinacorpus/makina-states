#!/usr/bin/env python
# generate python tags to be imported from inside and  outside the VM (from the hosts)
# main utility is to generate vim tags afterwards importing the .env in the shell
import os, sys
CWD = os.path.dirname(os.path.abspath('$(dirname $0)'))
open('tags.env', 'w').write((
"""#!/usr/bin/env bash
CWD="$PWD"
PRE=''
#echo $CWD
if [ x"${{PWD%%*VM*}}" = "x" ];then
    PRE="${{PWD%%\/VM\/*}}/VM"
fi
""".format() + '\n'.join(
        ['export PYTHONPATH="$PYTHONPATH:${PRE}' + a + '"'
         for a in sys.path
         if not 'states/bin' in a 
            and not 'lib/pymodules' in a
            and not '/lib/python' in a])
    + """
export PYTHONPATH="$(echo "${{PYTHONPATH}}"|sed -e "s/^://g"|sed -e "s/\\\\/\\\\//\\\\//g")"
""".format()
))
