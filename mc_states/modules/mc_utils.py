# -*- coding: utf-8 -*-
'''
.. _module_mc_utils:

mc_utils / Some usefull small tools
====================================
'''

# Import salt libs
import datetime
import copy
import os
import salt.utils.dictupdate
from pprint import pformat
import cProfile
import pstats
from salt.exceptions import SaltException
import crypt
import re
import logging
import salt.utils
from salt.utils.odict import OrderedDict
from salt.utils import yamldumper
import salt.loader
from mc_states import api

from salt.ext import six as six

import mc_states.utils
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from salt.utils.pycrypto import secure_password
import salt.utils.network
from salt.config import master_config, minion_config

_CACHE = {'mid': None}

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


_default_marker = object()
log = logging.getLogger(__name__)


def uniquify(*a, **kw):
    return api.uniquify(*a, **kw)


def odict(instance=True):
    if instance:
        return OrderedDict()
    return OrderedDict


def local_minion_id(force=False):
    '''
    search in running config root
    then in well known config mastersalt root
    then in well known config salt root
    then use regular salt function
    '''
    mid = _CACHE['mid']
    if mid and not force:
        return mid
    paths = api.uniquify([
        __opts__['config_dir'], '/etc/mastersalt', '/etc/salt'])
    for path in paths:
        for cfgn, fun in OrderedDict(
            [('master', master_config),
             ('minion', minion_config)]
        ).items():
            cfg = os.path.join(path, cfgn)
            if os.path.exists(cfg):
                try:
                    cfgo = fun(cfg)
                    mid = cfgo.get('id', None)
                    if mid.endswith('_master'):
                        mid = None
                except Exception:
                    pass
            if mid:
                break
        if mid:
            break
    # normally we should never hit this case as salt generates
    # internally during config parsing the minion id
    if not mid:
        mid = salt.utils.network.generate_minion_id()
    _CACHE['mid'] = mid
    return mid


def magicstring(thestr):
    """Convert any string to UTF-8 ENCODED one"""
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


def generate_stored_password(key, length=None, force=False, value=None):
    if length is None:
        length = 16
    reg = __salt__[
            'mc_macros.get_local_registry'](
                'local_passwords', registry_format='pack')
    sav = False
    if not key in reg:
        sav = True
    rootpw = reg.setdefault(key, __salt__['mc_utils.generate_password'](length))
    if force or not rootpw:
        rootpw = __salt__['mc_utils.generate_password'](length)
        sav = True
    if value is not None:
        rootpw = value
    reg[key] = rootpw
    __salt__['mc_macros.update_local_registry'](
        'local_passwords', reg, registry_format='pack')
    return rootpw


def generate_password(length=None):
    if length is None:
        length = 16
    return secure_password(length)


class _CycleError(Exception):
    """."""


def deepcopy(arg):
    return copy.deepcopy(arg)


def dictupdate(dict1, dict2):
    '''
    Merge two dictionnaries recursively

    test::

      salt '*' mc_utils.dictupdate '{foobar:
                  {toto: tata, toto2: tata2},titi: tutu}'
                  '{bar: toto, foobar: {toto2: arg, toto3: arg2}}'
      ----------
      bar:
          toto
      foobar:
          ----------
          toto:
              tata
          toto2:
              arg
          toto3:
              arg2
      titi:
          tutu
    '''
    if not isinstance(dict1, dict):
        raise SaltException(
            'mc_utils.dictupdate 1st argument is not a dictionnary!')
    if not isinstance(dict2, dict):
        raise SaltException(
            'mc_utils.dictupdate 2nd argument is not a dictionnary!')
    return salt.utils.dictupdate.update(dict1, dict2)


_marker = object()


def format_resolve(value,
                   original_dict=None,
                   global_tries=50,
                   this_call=0, topdb=False):
    """Resolve a dict of formatted strings, mappings & list to a valued dict
    Please also read the associated test::

        {"a": ["{b}", "{c}", "{e}"],
         "b": 1,
         "c": "{d}",
         "d": "{b}",
         "e": "{d}",
        }

        ====>
        {"a": ["1", "1", "{e}"],
         "b": 1,
         "c": "{d}",
         "d": "{b}",
         "e": "{d}",
        }

    """
    if not original_dict:
        original_dict = OrderedDict()
    if this_call == 0 and not original_dict and isinstance(value, dict):
        original_dict = value
    left = False
    cycle = True

    if isinstance(value, dict):
        new = OrderedDict()
        for key, val in value.items():
            val = format_resolve(val, original_dict, this_call=this_call + 1, topdb=topdb)
            new[key] = val
    elif isinstance(value, (list, tuple)):
        new = type(value)()
        for v in value:
            val = format_resolve(v, original_dict, this_call=this_call + 1, topdb=topdb)
            new = new + type(value)([val])
    elif isinstance(value, basestring):
        new = value
        if '/downloads' in new:
            topdb= True
        # do not directly call format to handle keyerror in original mapping
        # where we may have yet keyerrors
        if isinstance(original_dict, dict):
            for k in original_dict:
                reprk = k
                if not isinstance(reprk, basestring):
                    reprk = '{0}'.format(k)
                subst = '{' + reprk + '}'
                subst_val = original_dict[k]
                if subst in new:
                    if isinstance(subst_val, (list, dict)):
                        inner_new = format_resolve(
                            subst_val, original_dict, this_call=this_call + 1, topdb=topdb)
                        # composed, we take the repr
                        if new != subst:
                            new = new.replace(subst, str(inner_new))
                        # no composed value, take the original list
                        else:
                            new = inner_new
                    else:
                        if new != subst_val:
                            new = new.replace(subst,
                                              str(subst_val))
        if ('{' in new) and ('}' in new):
            i = 0
            while True:
                try:
                    this_call += 1
                    if this_call > 1000:
                        raise _CycleError('cycle')
                    new_val = format_resolve(
                        new, original_dict, this_call=this_call + 1, topdb=topdb)
                    new_braces = new.count('{'), new.count('}')
                    newval_braces = new_val.count('{'), new_val.count('}')
                    if new_braces == newval_braces:
                        break
                    else:
                        new = new_val
                except _CycleError:
                    cycle = True
                    break
            if ('{' in new) and ('}' in new):
                left = True
    else:
        new = value
    if left:
        if this_call == 0:
            for i in global_tries:
                new_val = format_resolve(
                    new, original_dict, this_call=this_call + 1, topdb=topdb)
                if (new == new_val) or cycle:
                    break
                else:
                    new = new_val
        else:
            while not cycle:
                new_val = format_resolve(
                    new, original_dict, this_call=this_call + 1, topdb=topdb)
                if (new == new_val) or (cycle):
                    break
                else:
                    new = new_val
    return new


def is_a_str(value):
    """."""
    return isinstance(value, six.string_types)


def is_a_bool(value):
    """."""
    return isinstance(value, bool)


def is_a_int(value):
    """."""
    return isinstance(value, int)


def is_a_float(value):
    """."""
    return isinstance(value, float)


def is_a_complex(value):
    """."""
    return isinstance(value, complex)


def is_a_long(value):
    """."""
    return isinstance(value, long)


def is_a_number(value):
    return (
        is_a_int(value)
        or is_a_float(value)
        or is_a_complex(value)
        or is_a_long(value)
    )


def is_a_set(value):
    """."""
    return isinstance(value, set)


def is_a_tuple(value):
    """."""
    return isinstance(value, tuple)


def is_a_list(value):
    """."""
    return isinstance(value, list)


def is_a_dict(value):
    """."""
    return isinstance(value, dict)


def is_iter(value):
    return (
        is_a_list(value)
        or is_a_dict(value)
        or is_a_tuple(value)
        or is_a_set(value)
    )


def traverse_dict(data, key, delimiter=salt.utils.DEFAULT_TARGET_DELIM):
    '''
    Handle the fact to traverse dicts with '.' as it was an old
    default and makina-states relies a lot on it

    This restore the old behavior of something that can be traversed

    makina-states.foo:
        bar:
            c: true

    can be traversed with makina-states.foo.bar.c
    '''
    delimiters = [delimiter, salt.utils.DEFAULT_TARGET_DELIM, ':', '.']
    ret = dv = '_|-'
    for dl in delimiters:
        for cdl in reversed(delimiters):
            ret = salt.utils.traverse_dict(data, key, dv, delimiter=dl)
            if ret != dv:
                return ret
            if cdl in key and dl not in key:
                nkey = key.replace(cdl, dl)
                ret = salt.utils.traverse_dict(data, nkey, dv, delimiter=dl)
                if ret != dv:
                    return ret
                # if the dict is not at the end, we try to progressivily
                # combine the delimiters from the start of the key
                # a.c.d.e will be tested then for
                # a.c:d:e will be tested then for
                # a.c.d:e will be tested then for
                # we do not test the last element as it is the exact key !
                for i in range(key.count(cdl)-1):
                    dkey = nkey.replace(dl, cdl, i+1)
                    ret = salt.utils.traverse_dict(data, dkey, dv, delimiter=dl)
                    if ret != dv:
                        return ret
    return ret


def get(key, default='',
        local_registry=None, registry_format='pack',
        delimiter=salt.utils.DEFAULT_TARGET_DELIM):
    '''
    Same as 'config.get' but with different retrieval order.

    This routine traverses these data stores in this order:

        - Local minion config (opts)
        - Minion's pillar
        - Dict:
            - passed in local_registry argument
            - or automaticly loaded global registries
        - Minion's grains
        - Master config

    CLI Example:

    .. code-block:: bash

        salt '*' mc_utils.get pkg:apache
    '''
    _s, _g, _p, _o = __salt__, __grains__, __pillar__, __opts__
    if local_registry is None:
        local_prefs = [(a, 'makina-states.{0}.'.format(a))
                       for a in api._GLOBAL_KINDS]
        for reg, pref in local_prefs:
            if key.startswith(pref):
                local_registry = reg
                break
    if isinstance(local_registry, basestring):
        local_registry = _s['mc_macros.get_local_registry'](
            local_registry, registry_format=registry_format)
    ret = traverse_dict(_o, key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    ret = traverse_dict(_p, key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    if local_registry is not None:
        ret = traverse_dict(local_registry, key, delimiter=delimiter)
        if ret != '_|-':
            return ret
    ret = traverse_dict(_g, key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    ret = traverse_dict(_p.get('master', {}), key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    return default


def get_uniq_keys_for(prefix):
    """Return keys for prefix:
        - if prefix is in conf
        - All other keys of depth + 1


        With makina.foo prefix:

        - returns makina.foo
        - returns makina.foo.1
        - dont returns makina.foo.1.1
        - dont returns makina
        - dont returns makina.other
    """

    keys = OrderedDict()
    for mapping in (__pillar__,
                    __grains__):
        skeys = []
        for k in mapping:
            if k.startswith(prefix):
                testn = k[len(prefix):]
                try:
                    if testn.index('.') < 2:
                        skeys.append(k)
                except:
                    continue
        skeys.sort()
        for k in skeys:
            keys[k] = mapping[k]
    return keys


def defaults(prefix,
             datadict,
             ignored_keys=None,
             overridden=None,
             noresolve=False,
             firstcall=True):
    '''
    Magic defaults settings configuration getter

    - Get the "prefix" value from the configuration (pillar/grain)
    - Then overrides it with  "datadict" mapping recursively
        - If
            - the datadict contains a key "{prefix}-overrides
            - AND value is a dict or  a list:

                Take that as a value for the the value /subtree

        - If the datadict contains a key "{prefix}":
            - If a list: append to the list the default list in conf
            - Elif a dict: update the default dictionnary with the one in conf
            - Else take that as a value if the value is not a mapping or a list
    '''
    if not ignored_keys:
        ignored_keys = []
    if firstcall:
        global_pillar = copy.deepcopy(
            __salt__['mc_utils.get'](prefix))
        if isinstance(global_pillar, dict):
            for k in [a for a in ignored_keys if a in global_pillar]:
                if k in global_pillar:
                    del global_pillar[k]
            datadict = __salt__['mc_utils.dictupdate'](datadict, global_pillar)

    # if we overrided only keys of a dict
    # but this dict is an empty dict in the default mapping
    # be sure to load them inside this dict
    items = get_uniq_keys_for(prefix)
    dotedprefix = '{0}.'.format(prefix)
    for fullkey in items:
        key = dotedprefix.join(fullkey.split(dotedprefix)[1:])
        val = items[fullkey]
        if isinstance(datadict, dict):
            curval = datadict.get(key, None)
            if isinstance(curval, dict):
                val = __salt__['mc_utils.dictupdate'](curval, val)
            elif isinstance(curval, (list, set)):
                if val is not None:
                    curval.extend(val)
                val = curval
            datadict[key] = val
    if overridden is None:
        overridden = OrderedDict()
    if prefix not in overridden:
        overridden[prefix] = OrderedDict()
    pkeys = {}
    for a in datadict:
        if a not in ignored_keys:
            to_unicode = False
            for i in prefix, a:
                if isinstance(i, unicode):
                    to_unicode = True
                    break
            k = '{0}.{1}'.format(magicstring(prefix), magicstring(a))
            if to_unicode:
                k = k.decode('utf-8')
            pkeys[a] = (k , datadict[a])
    for key, value_data in pkeys.items():
        value_key, default_value = value_data
        # special key to completly overrides the dictionnary
        value = __salt__['mc_utils.get'](
            value_key + "-overrides", _default_marker)
        if value is not _default_marker:
            overridden[prefix][key] = value
        else:
            value = __salt__['mc_utils.get'](value_key, _default_marker)
        if not isinstance(default_value, list) and value is _default_marker:
            value = default_value
        if isinstance(default_value, list):
            if key in overridden[prefix]:
                value = overridden[prefix][key]
            else:
                nvalue = default_value[:]
                if (
                    value
                    and (value != nvalue)
                    and (value is not _default_marker)
                ):
                    if nvalue is None:
                        nvalue = []
                    nvalue.extend(value)
                value = nvalue
        elif isinstance(value, dict):
            # recurvive and conservative dictupdate
            ndefaults = defaults(value_key,
                                 value,
                                 overridden=overridden,
                                 firstcall=firstcall)
            if overridden[value_key]:
                for k, value in overridden[value_key].items():
                    default_value[k] = value
            # override speific keys values handle:
            # eg: makina-states.services.firewall.params.RESTRICTED_SSH = foo
            # eg: makina-states.services.firewall.params:
            #        foo: var
            for k, subvalue in get_uniq_keys_for(value_key).items():
                ndefaults[k.split('{0}.'.format(value_key))[1]] = subvalue
            value = __salt__['mc_utils.dictupdate'](default_value, ndefaults)

        datadict[key] = value
        for k, value in overridden[prefix].items():
            datadict[k] = value
    if not noresolve:
        datadict = format_resolve(datadict)
    return datadict


def sanitize_kw(kw):
    ckw = copy.deepcopy(kw)
    for k in kw:
        if ('__pub_' in k) and (k in ckw):
            ckw.pop(k)
    return ckw


def cyaml_load(*args, **kw):
    args = list(args)
    close = False
    if args and isinstance(args[0], basestring) and os.path.exists(args[0]):
        args[0] = open(args[0])
        close = True
    ret = yaml.load(Loader=Loader, *args,
                    **__salt__['mc_utils.sanitize_kw'](kw))
    if close:
        args[0].close()
    return ret


def cyaml_dump(*args, **kw):
    args = list(args)
    close = False
    if args and isinstance(args[0], basestring) and os.path.exists(args[0]):
        args[0] = open(args[0])
        close = True
    ret = yaml.dump(Dumper=Dumper, *args,
                    **__salt__['mc_utils.sanitize_kw'](kw))
    if close:
        args[0].close()
    return ret


def yaml_dump(data, flow=False):
    """."""
    content = yaml.dump(
        data,
        default_flow_style=flow,
        Dumper=yamldumper.SafeOrderedDumper)
    content = content.replace('\n', ' ')
    return yencode(content)


def salt_root():
    '''get salt root from either pillar or opts (minion or master)'''
    salt = __salt__['mc_salt.settings']()
    return salt['c']['o']['saltRoot']


def msr():
    '''get salt root from either pillar or opts (minion or master)'''
    salt = __salt__['mc_salt.settings']()
    return salt['c']['o']['msr']


def iyaml_dump(data):
    """."""
    return yaml_dump(data, flow=True)


def json_dump(data, pretty=False):
    """."""
    return api.json_dump(data, pretty=pretty)


def json_load(data):
    """."""
    return api.json_load(data)


def yencode(string):
    """."""
    return api.yencode(string)


def file_read(fic):
    """."""
    data = ''
    with open(fic, 'r') as f:
        data = f.read()
    return data


def unix_crypt(passwd):
    '''Encrypt the stringed password in the unix crypt format (/etc/shadow)'''
    return crypt.crypt(passwd, '$6$SALTsalt$')


def sls_available(sls, pillar=True):
    ret = True
    if pillar:
        root = __opts__['pillar_roots']['base'][0]
    else:
        root = __opts__['pillar_roots']['base'][0]
    fp = os.path.join(root, sls.replace('.', '/') + '.sls')
    try:
        ret = os.path.exists(fp)
    except OSError:
        ret = False
    return ret


def indent(tstring, spaces=16, char=' '):
    data = ''
    for ix, i in enumerate(tstring.split('\n')):
        if ix > 0:
            data += char * spaces
        data += i + '\n'
    return data


def profile(func, *args, **kw):
    if not __opts__.get('ms_profile_enabled', False):
        raise Exception('Profile not enabled')
    kw = copy.deepcopy(kw)
    for i in [a for a in kw if a.startswith('__')]:
        kw.pop(i, None)
    pr = cProfile.Profile()
    pr.enable()
    ret = __salt__[func](*args, **kw)
    pr.disable()
    if not os.path.isdir('/tmp/stats'):
        os.makedirs('/tmp/stats')
    ficp = '/tmp/stats/{0}.pstats'.format(func)
    fico = '/tmp/stats/{0}.dot'.format(func)
    ficcl = '/tmp/stats/{0}.calls.stats'.format(func)
    ficn = '/tmp/stats/{0}.cumulative.stats'.format(func)
    fict = '/tmp/stats/{0}.total.stats'.format(func)
    for i in [ficp, fico, ficn, fict, ficcl]:
        if os.path.exists(i):
            os.unlink(i)
    pr.dump_stats(ficp)
    with open(ficn, 'w') as fic:
        ps = pstats.Stats(
            pr, stream=fic).sort_stats('cumulative')
        ps.print_stats()
    with open(ficcl, 'w') as fic:
        ps = pstats.Stats(
            pr, stream=fic).sort_stats('calls')
        ps.print_stats()
    with open(fict, 'w') as fic:
        ps = pstats.Stats(
            pr, stream=fic).sort_stats('tottime')
        ps.print_stats()
    os.system(
        '/srv/mastersalt/makina-states/bin/pyprof2calltree '
        '-i {0} -o {1}'.format(ficp, fico))
    return ret, ficp, fico, ficn, ficcl, fict


def invalidate_memoize_cache(*args, **kw):
    return mc_states.utils.invalidate_memoize_cache(*args, **kw)


def manage_file(name, **kwargs):
    '''
    Easier wrapper to file.manage_file
    '''
    for i in [a for a in kwargs if '__' in a]:
        kwargs.pop(i, None)
    log.error(kwargs.keys())
    kwargs.setdefault('mode', '755')
    kwargs.setdefault('backup', None)
    kwargs.setdefault('contents', None)
    kwargs.setdefault('makedirs', True)
    kwargs.setdefault('user', 'root')
    kwargs.setdefault('group', 'root')
    kwargs.setdefault('saltenv', 'base')
    kwargs.setdefault('ret', None)
    kwargs.setdefault('sfn', None)
    kwargs.setdefault('source', None)
    kwargs.setdefault('source_sum', None)
    return __salt__['file.manage_file'](name, **kwargs)


def _outputters(outputter=None):
    outputters = salt.loader.outputters(__opts__)
    if outputter:
        return outputters[outputter]
    return outputters


def output(mapping, raw=False, outputter='highstate'):
    '''
    This return a formatted output
    '''
    color = __opts__.get('color', None)
    slashre = re.compile('[\\\]+', re.S | re.U | re.X)
    __opts__['color'] = not raw
    try:
        if isinstance(mapping, dict) and (outputter == 'highstate'):
            ret = _outputters(outputter)({'local': mapping})
        else:
            ret = _outputters(outputter)(mapping)
    except MemoryError:
        # try to print out something in RAW MODE
        mmapping = copy.deepcopy(mapping)
        # ugly hack inside:
        # on error while display message
        # with recursive \\, just try to strip them
        # and reuse the outputter
        try:
            if not isinstance(mmapping, dict):
                raise ValueError('not a dict, trying raw output')
            for state in [
                i for i in mmapping
                if isinstance(mmapping[i], dict)
            ]:
                if not isinstance(mmapping[state], dict):
                    continue
                for k in [
                    j for j in mmapping[state]
                    if isinstance(mapping[state][j], basestring)
                ]:
                    mmapping[state][k] = slashre.sub('', mmapping[state][k])
            if outputter == 'highstate':
                ret = _outputters(outputter)({'local': mmapping})
            else:
                ret = _outputters(outputter)(mmapping)
        except Exception:
            # try to print out something in RAW MODE
            # without outputter formatting
            try:
                ret = pformat(mmapping)
            except Exception:
                try:
                    ret = u"{0}".format(mmapping)
                except Exception:
                    try:
                        ret = "{0}".format(mmapping)
                    except Exception:
                        raise
    __opts__['color'] = color
    return ret
#
