from __future__ import (absolute_import, division, print_function)

import json

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleUndefinedVariable

__metaclass__ = type


class ActionModule(ActionBase):
    '''Print statements during execution'''

    TRANSFERS_FILES = False
    VALID_ARGS = set(['msg', 'var', 'json'])

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        for arg in self._task.args:
            if arg not in self.VALID_ARGS:
                return {"failed": True,
                        "msg": "'%s' is not a valid option in msvar" % arg}
        if not any([
            'var' in self._task.args,
            'json' in self._task.args,
            'msg' in self._task.args,
        ]):
            result = 'Hello world!'
        if 'json' in self._task.args:
            result = json.loads(self._task.args['json'])
        if 'msg' in self._task.args:
            result = self._task.args['msg']
        if 'var' in self._task.args:
            result = self._templar.template(
                self._task.args['var'],
                convert_bare=True,
                fail_on_undefined=True,
                bare_deprecated=False)
            if result == self._task.args['var']:
                raise AnsibleUndefinedVariable
        result = {'result': result, '_ansible_verbose_always': True}
        return result
