# -*- coding: utf-8 -*-
__doc__ = '''
.. _module_mc_dumper:

mc_dumper / Some useful wrappers to dump/load values
====================================================


'''
__docformat__ = 'restructuredtext en'

import os
import yaml
import msgpack
import copy
try:
    from yaml import (
        CLoader as yLoader,
        CDumper as yDumper)
except ImportError:
    from yaml import (
        Loader as yLoader,
        Dumper as yDumper)
from salt.utils import yamldumper
from mc_states import api


def sanitize_kw(kw):
    ckw = copy.deepcopy(kw)
    for k in kw:
        if ('__pub_' in k) and (k in ckw):
            ckw.pop(k)
    return ckw


def yencode(string, *args, **kw):
    '''
    wrapper to :meth:`~mc_states_api.yencode`
    '''
    return api.yencode(string)


def cyaml_load(*args, **kw):
    '''
    Load a value encoded in yaml

    The first positional argument is either a yaml value
    or a path filename.
    '''
    args = list(args)
    close = False
    ret = None
    kw.setdefault('Loader', yLoader)
    if args and isinstance(args[0], basestring) and os.path.exists(args[0]):
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
    '''
    return api.json_load(data)


def json_dump(data, pretty=False, *args, **kw):
    '''
    encode a string in json
    '''
    return api.json_dump(data, pretty=pretty)
