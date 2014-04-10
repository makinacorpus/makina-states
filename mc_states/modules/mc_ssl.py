#!/usr/bin/env python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_ssl:

mc_ssl / ssl registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ssl

'''
# Import python libs
import logging
import mc_states.utils

__name = 'ssl'

log = logging.getLogger(__name__)


def is_reverse_proxied():
    return __salt__['mc_cloud.is_vm']()


def settings():
    '''
    ssl registry

    country
        country
    st
        st
    l
        l
    o
        organization
    cn
        common name
    email
        mail
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        # users data
        # SSL settings for reuse in states
        country = saltmods['grains.get']('defaultlanguage')
        if country:
            country = country[:2].upper()
        else:
            country = 'fr'
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.ssl', {
                'country': country,
                'st': 'Pays de Loire',
                'l': 'NANTES',
                'o': 'NANTES',
                'cn': grains['fqdn'],
                'email': grains['fqdn'],
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
