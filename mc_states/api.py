#!/usr/bin/env python
'''
.. _mc_states_api:

mc_states_api / general API functions
=======================================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import json
import re


def uniquify(seq):
    '''uniquify a list'''
    seen = set()
    return [x
            for x in seq
            if x not in seen and not seen.add(x)]


def splitstrip(string):
    '''Strip empty lines'''
    return '\n'.join(
        [a for a in string.splitlines() if a.strip()])


def msplitstrip(mapping, keys=None):
    '''Make the defined keys values stripped of
    their empty lines'''
    if not keys:
        keys = ['trace', 'comment', 'raw_comment']
    for k in keys:
        if k in mapping:
            mapping[k] = splitstrip(mapping[k])
    return mapping


def indent(string_or_list, indent='    ', sep='\n'):
    if isinstance(string_or_list, basestring):
        string_or_list = string_or_list.splitlines()
    if ''.join(string_or_list).strip():
        string_or_list = indent + '{1}{0}'.format(
            indent, sep).join(string_or_list)
    return string_or_list


def yencode(string):
    if isinstance(string, basestring):
        re_y = re.compile(' \.\.\.$', re.M)
        string = re_y.sub('', string)
    return string


def json_dump(data):
    content = json.dumps(data)
    content = content.replace('\n', ' ')
    return yencode(content)
# vim:set et sts=4 ts=4 tw=80:
