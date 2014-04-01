# -*- coding: utf-8 -*-
'''
.. _module_mc_utils:

mc_utils / Some usefull small tools
====================================
'''

# Import salt libs
import salt.utils.dictupdate
from salt.exceptions import SaltException
import crypt
import getpass
import pwd
import re
import salt.utils
from salt.utils.odict import OrderedDict
import yaml
from salt.utils import yamldumper

import json

_default_marker = object()


class _CycleError(Exception):
    """."""


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
                   this_call=0):
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
            val = format_resolve(val, original_dict, this_call=this_call + 1)
            new[key] = val
    elif isinstance(value, (list, tuple)):
        new = type(value)()
        for v in value:
            val = format_resolve(v, original_dict, this_call=this_call + 1)
            new = new + type(value)([val])
    elif isinstance(value, basestring):
        new = value
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
                            subst_val, original_dict, this_call=this_call + 1)
                        # composed, we take the repr
                        if new != subst:
                            new = new.replace(subst, str(inner_new))
                        # no composed value, take the original list
                        else:
                            new = inner_new
                    else:
                        new = new.replace(subst, str(subst_val))
        if ('{' in new) and ('}' in new):
            i = 0
            while True:
                try:
                    this_call += 1
                    if this_call > 1000:
                        raise _CycleError('cycle')
                    new_val = format_resolve(
                        new, original_dict, this_call=this_call + 1)
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
                    new, original_dict, this_call=this_call + 1)
                if (new == new_val) or cycle:
                    break
                else:
                    new = new_val
        else:
            while not cycle:
                new_val = format_resolve(
                    new, original_dict, this_call=this_call + 1)
                if (new == new_val) or (cycle):
                    break
                else:
                    new = new_val
    return new


def is_a_set(value):
    return isinstance(value, set)


def is_a_tuple(value):
    return isinstance(value, tuple)


def is_a_list(value):
    return isinstance(value, list)


def is_a_dict(value):
    return isinstance(value, dict)


def is_iter(value):
    return (
        is_a_list(value)
        or is_a_dict(value)
        or is_a_tuple(value)
        or is_a_set(value)
    )


def get(key, default='', local_registry=None):
    '''Same as 'config.get' but with different retrieval order.

    This routine traverses these data stores in this order:

        - Local minion config (opts)
        - Minion's pillar
        - Dict passed in local_registry argument
        - Minion's grains
        - Master config

    CLI Example:

    .. code-block:: bash

        salt '*' mc_utils.get pkg:apache
    '''
    ret = salt.utils.traverse_dict(__opts__, key, '_|-')
    if ret != '_|-':
        return ret
    ret = salt.utils.traverse_dict(__pillar__, key, '_|-')
    if ret != '_|-':
        return ret
    if local_registry is not None:
        ret = salt.utils.traverse_dict(local_registry, key, '_|-')
        if ret != '_|-':
            return ret
    ret = salt.utils.traverse_dict(__grains__, key, '_|-')
    if ret != '_|-':
        return ret
    ret = salt.utils.traverse_dict(__pillar__.get('master', OrderedDict()),
                                   key, '_|-')
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
        global_pillar =  __salt__['mc_utils.get'](prefix)
        if isinstance(global_pillar, dict):
            for k in [a for a in ignored_keys if a in global_pillar]:
                del global_pillar[k]
            datadict = __salt__['mc_utils.dictupdate'](datadict, global_pillar)
    if overridden is None:
        overridden = OrderedDict()
    if not prefix in overridden:
        overridden[prefix] = OrderedDict()
    for key in [a for a in datadict if not a in ignored_keys]:
        default_value = datadict[key]
        value_key = '{0}.{1}'.format(prefix, key)
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
                if value is not _default_marker:
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
    return format_resolve(datadict)


def yaml_dump(data):
    content = yaml.dump(
        data,
        default_flow_style=False,
        Dumper=yamldumper.SafeOrderedDumper)
    content = content.replace('\n', ' ')
    return yencode(content)


def json_dump(data):
    content = json.dumps(data)
    content = content.replace('\n', ' ')
    return yencode(content)


def yencode(string):
    if isinstance(string, basestring):
        re_y = re.compile(' \.\.\.$', re.M)
        string = re_y.sub('', string)
    return string


def unix_crypt(passwd):
    '''Encrypt the stringed password in the unix crypt format (/etc/shadow)'''
    return crypt.crypt(passwd, '$6$SALTsalt$')

#
