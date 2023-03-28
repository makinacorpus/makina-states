# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
'''
.. _module_mc_dumper:

mc_dumper / Some useful wrappers to dump/load values
====================================================


'''


import os
import yaml
import msgpack
try:
    from yaml import (
        CLoader as yLoader,
        CDumper as yDumper)
except ImportError:
    from yaml import (
        Loader as yLoader,
        Dumper as yDumper)
from salt.utils import yamldumper
from salt.utils.odict import OrderedDict
from mc_states import api
from mc_states import saltapi

six = saltapi.six


def sanitize_kw(kw):
    return saltapi.sanitize_kw(kw, omit=['is_file'])


def yencode(string, *args, **kw):
    '''
    wrapper to :meth:`~mc_states_api.yencode`
    '''
    return api.yencode(string)


def first_arg_is_file(*args, **kwargs):
    is_file = kwargs.get('is_file', None)
    if is_file is None:
        is_file = (
            args and
            isinstance(args[0], six.string_types) and
            os.path.exists(args[0]))
    return bool(is_file)


def cyaml_load(*args, **kw):
    '''
    Load a value encoded in yaml

    The first positional argument is either a yaml value
    or a path filename.

    WARNING:  THIS FUNCTION SHOULD WORK WITHOUT SALT
    '''
    args = list(args)
    close = False
    ret = None
    kw.setdefault('Loader', yLoader)
    is_file = first_arg_is_file(*args, **kw)
    if is_file:
        args[0] = open(args[0])
        close = True
    try:
        ret = yaml.load(*args, **sanitize_kw(kw))
    finally:
        if close:
            args[0].close()
    return ret


def yaml_load(*args, **kw):
    '''
    Wrapper to cyaml_load

    WARNING:  THIS FUNCTION SHOULD WORK WITHOUT SALT
    '''
    return cyaml_load(*args, **kw)


def yaml_dump(data,
              flow=None,
              nonewline=None,
              *args,
              **kw):
    '''
    encode a value with yaml using saltstack yaml dumper
    '''
    args = list(args)
    args.insert(0, data)
    if nonewline is None:
        nonewline = False
    if flow is None:
        flow = False
    kw.setdefault('Dumper',
                  yamldumper.SafeOrderedDumper)
    kw.setdefault('default_flow_style', flow)
    content = yaml.dump(*args, **sanitize_kw(kw))
    if nonewline:
        content = content.replace('\n', ' ')
    return api.yencode(content)


def cyaml_dump(*args, **kw):
    '''
    Encode a value in yaml with raw c Yaml dumper
    '''
    kw.setdefault('Dumper', yDumper)
    return yaml_load(*args, **kw)


def old_yaml_dump(data,
                  flow=None,
                  nonewline=None,
                  *args,
                  **kw):
    '''
    encode a value with yaml

    DO NOT TOUCH TO NONEWLINE=True as default
    (RETROCOMPAT WITH STATES)
    '''
    if nonewline is None:
        nonewline = True
    kw['nonewline'] = nonewline
    kw['flow'] = flow
    return yaml_dump(data, **kw)


def iyaml_dump(data, flow=None, *args, **kw):
    '''
    load a value in yaml
    '''
    if flow is None:
        flow = True
    return yaml_dump(data, flow=flow)


def msgpack_load(data, *args, **kw):
    '''
    loade a msgpacked value
    '''
    if not data:
        return {}
    value = msgpack.unpackb(data)['value']
    return value


def msgpack_dump(data, *args, **kw):
    '''
    encode a value with msgpack
    '''
    content = msgpack.packb({'value': data})
    return content


def json_load(data, *args, **kw):
    '''
    load a json string

    WARNING:  THIS FUNCTION SHOULD WORK WITHOUT SALT
    '''
    return api.json_load(data)


def json_dump(data, pretty=False, *args, **kw):
    '''
    encode a string in json
    '''
    return api.json_dump(data, pretty=pretty)


def setup_yaml_dumper(yaml):
    def represent_dict_order(self, data):
        ret = self.represent_mapping('tag:yaml.org,2002:map', data)
        return ret
    rep = yaml.representer
    rep.add_representer(OrderedDict, represent_dict_order)
    rep.add_representer(
        list,
        lambda d, data: d.represent_sequence('tag:yaml.org,2002:seq', data))
    rep.add_representer(
        tuple,
        lambda d, data: d.represent_sequence('tag:yaml.org,2002:seq', data))
    return yaml
