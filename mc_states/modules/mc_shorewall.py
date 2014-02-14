# -*- coding: utf-8 -*-
'''
mc_shorewall / shorewall functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'shorewall'

log = logging.getLogger(__name__)


def settings():
    '''
    shorewall settings

    makina-states.services.shorewall.enabled: activate shorewall

    It will also assemble pillar slugs to make powerfull firewalls
    by parsing all **\*-makina-shorewall** pillar entries to load the special shorewall structure:

    All entries are merged in the lexicograpĥical order

    item-makina-shorewall
        interfaces
            TBD
        rules
            TBD
        params
            TBD
        policies
            TBD
        zones
            TBD
        masqs
            TBD

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = localsettings['locations']
        data = {}
        data['shw_enabled'] = (
            __salt__['mc_utils.get'](
                'makina-states.services.shorewall.enabled', False))
        data['shwIfformat'] = 'FORMAT 2'
        if grains['os'] not in ['Debian']:
            data['shwIfformat'] = '?'
        data['shwPolicies'] = shwPolicies = []
        data['shwZones'] = shwZones = {}
        data['shwInterfaces'] = shwInterfaces = {}
        data['shwParams'] = shwParams = {}
        data['shwMasqs'] = shwMasqs = {}
        data['shwRules'] = shwRules = {}
        data['shwDefaultState'] = shwDefaultState = 'new'
        data['shwData'] = {
            'interfaces': shwInterfaces,
            'rules': shwRules,
            'params': shwParams,
            'policies': shwPolicies,
            'zones': shwZones,
            'masqs': shwMasqs,
            'ifformat': data['shwIfformat'],
        }
        for sid, shorewall in pillar.items():
            if sid.endswith('makina-shorewall'):
                shwlocrules = shorewall.get('rules', {})
                for i in shwlocrules:
                    section = i.get('section', shwDefaultState).upper()
                    if section not in shwRules:
                        shwRules.update({section: []})
                    shwRules[section].append(i)
                shwInterfaces.update(shorewall.get('interfaces', {}))
                shwMasqs.update(shorewall.get('masqs', {}))
                shwParams.update(shorewall.get('params', {}))
                shwZones.update(shorewall.get('zones', {}))
                shwPolicies.extend(shorewall.get('policies', []))
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
