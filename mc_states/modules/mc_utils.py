# -*- coding: utf-8 -*-
'''
Some usefull small tools
============================================

'''

# Import salt libs
import salt.utils.dictupdate
from salt.exceptions import SaltException
import salt.utils


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
       Please also read the associated test
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
        original_dict = {}
    if this_call == 0 and not original_dict and isinstance(value, dict):
        original_dict = value
    left = False
    cycle = True
    if isinstance(value, dict):
        new = {}
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
                subst = '{' + k + '}'
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


def get(key, default=''):
    '''
    .. versionadded: 0.14.0
    Same as 'config.get' but with different retrieval order:

    This routine traverses these data stores in this order:

    - Local minion config (opts)
    - Minion's pillar
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
    ret = salt.utils.traverse_dict(__grains__, key, '_|-')
    if ret != '_|-':
        return ret
    ret = salt.utils.traverse_dict(__pillar__.get('master', {}), key, '_|-')
    if ret != '_|-':
        return ret
    return default


def defaults(prefix, datadict):
    for key, default in datadict.copy().items():
        value_key = '{0}.{1}'.format(prefix, key)
        value =  __salt__['mc_utils.get'](value_key , default)
        if isinstance(value, dict):
            value = defaults(value_key, value)
        datadict[key] = value
    return format_resolve(datadict)

#
