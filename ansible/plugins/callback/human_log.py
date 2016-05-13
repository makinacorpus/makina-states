#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# https://raw.githubusercontent.com/n0ts/ansible-human_log/master/human_log.py
# Inspired from: https://github.com/redhat-openstack/khaleesi/blob/master/plugins/callbacks/human_log.py
# Further improved support Ansible 2.0

# set HUMAN_NOLOG to deactivate human log

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import six
import datetime
import pprint
from ansible.plugins.callback import CallbackBase

# Fields to reformat output for
FIELDS = ['cmd',
          'diff',
          'changes',
          'src',
          'module_args',
          'invocation',
          'block',
          'command',
          'start',
          'end',
          'delta',
          'msg',
          'stdout',
          'stderr',
          'salt_out',
          'saltout',
          'results']

try:
    import simplejson as json
except ImportError:
    import json

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


def magicstring(thestr):
    """
    Convert any string to UTF-8 ENCODED one
    """
    if not HAS_CHARDET:
        log.error('No chardet support !')
        return thestr
    seek = False
    if (
        isinstance(thestr, (int, float, long,
                            datetime.date,
                            datetime.time,
                            datetime.datetime))
    ):
        thestr = "{0}".format(thestr)
    if isinstance(thestr, unicode):
        try:
            thestr = thestr.encode('utf-8')
        except Exception:
            seek = True
    if seek:
        try:
            detectedenc = chardet.detect(thestr).get('encoding')
        except Exception:
            detectedenc = None
        if detectedenc:
            sdetectedenc = detectedenc.lower()
        else:
            sdetectedenc = ''
        if sdetectedenc.startswith('iso-8859'):
            detectedenc = 'ISO-8859-15'

        found_encodings = [
            'ISO-8859-15', 'TIS-620', 'EUC-KR',
            'EUC-JP', 'SHIFT_JIS', 'GB2312', 'utf-8', 'ascii',
        ]
        if sdetectedenc not in ('utf-8', 'ascii'):
            try:
                if not isinstance(thestr, unicode):
                    thestr = thestr.decode(detectedenc)
                thestr = thestr.encode(detectedenc)
            except Exception:
                for idx, i in enumerate(found_encodings):
                    try:
                        if not isinstance(thestr, unicode) and detectedenc:
                            thestr = thestr.decode(detectedenc)
                        thestr = thestr.encode(i)
                        break
                    except Exception:
                        if idx == (len(found_encodings) - 1):
                            raise
    if isinstance(thestr, unicode):
        thestr = thestr.encode('utf-8')
    thestr = thestr.decode('utf-8').encode('utf-8')
    return thestr



def nlstrip(val):
    if not val.startswith('\n'):
        val = val.lstrip()
    return val



def indent_string(val, indent_level, indenter=' '):
    indent = indenter * indent_level
    out = []
    for i in val.splitlines():
        out.append('{0}{1}'.format(indent, magicstring(i)))
    return '\n'.join(out)


class CallbackModule(CallbackBase):
    '''
    Ansible callback plugin for human-readable result logging
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'human_log'
    CALLBACK_NEEDS_WHITELIST = False

    def _output(self, val, indent=1):
        out, end = '', None
        # Strip unicode
        if isinstance(val, dict):
            out += '{'
            for i, val2 in six.iteritems(val):
                if not out.endswith('\n'):
                    out += '\n'
                out += indent_string('{0}: '.format(i), indent+1)
                out += nlstrip(self._output(val2, indent+2))
            end = '}'
        elif isinstance(val, (list, tuple, set)):
            out += '['
            for i in val:
                if not out.endswith('\n'):
                    out += '\n'
                out += indent_string(
                    '- {0}'.format(nlstrip(self._output(i))), indent+1)
            end = ']'
        else:
            try:
                sindent = indent
                sval = "{0}".format(val)
                if sval.count('\n') > 1 and indent > 1:
                    # dict/iterable element, we nest an indented string for
                    # better output
                    out += '\n'
                    sindent += 1
                out += indent_string(sval, sindent)
            except (Exception,) as exc:
                try:
                    out += '<NOT FORMATABLE VALUE: {0}>'.format(exc)
                except Exception:
                    out += '<NOT FORMATABLE VALUE>'
        if end:
            if val:
                if not out.endswith('\n'):
                    out += '\n'
                out += indent_string(end, indent-1)
            else:
                out += end
        return out

    def human_log(self, data):
        no_display = os.environ.get('HUMAN_NOLOG', '')
        if no_display:
            return
        if isinstance(data, dict):
            ndata = {}
            for field, val in six.iteritems(data):
                fields = data.get('_ansible_human_log_fields', FIELDS[:])
                if field not in fields:
                    continue
                no_log = d_no_log = data.get('_ansible_no_log')
                if isinstance(val, dict):
                    no_log = val.get('_ansible_no_log', d_no_log)
                if not no_log:
                    ndata[field] = val
            if ndata:
                print(self._output(ndata))

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.human_log(res)

    def runner_on_ok(self, host, res):
        self.human_log(res)

    def runner_on_unreachable(self, host, res):
        self.human_log(res)

    def runner_on_async_poll(self, host, res, jid, clock):
        self.human_log(res)

    def runner_on_async_ok(self, host, res, jid):
        self.human_log(res)

    def runner_on_async_failed(self, host, res, jid):
        self.human_log(res)

    ####### V2 METHODS ######
    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.human_log(result._result)

    def v2_runner_on_ok(self, result):
        self.human_log(result._result)

    def v2_runner_on_unreachable(self, result):
        self.human_log(result._result)

    def v2_runner_on_async_poll(self, result):
        self.human_log(result._result)

    def v2_runner_on_async_ok(self, host, result):
        self.human_log(result._result)

    def v2_runner_on_async_failed(self, result):
        self.human_log(result._result)

    def v2_playbook_on_item_failed(self, result):
        self.human_log(result._result)

    def v2_runner_item_on_ok(self, result):
        self.human_log(result._result)

    def v2_runner_item_on_failed(self, result):
        self.human_log(result._result)
