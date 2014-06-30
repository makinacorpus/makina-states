# -*- coding: utf-8 -*-
'''

.. _module_mc_mumble:

mc_mumble / mumble registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_mumble

'''
# Import python libs
import logging
import copy
import mc_states.utils
from salt.utils.pycrypto import secure_password

__name = 'mumble'

log = logging.getLogger(__name__)


def settings():
    '''
    mumble registry

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        local_conf = __salt__['mc_macros.get_local_registry'](
            'mumble', registry_format='pack')
        supassword = local_conf.get('supassword', secure_password(32))
        htpassword = local_conf.get('htpassword', secure_password(32))
        locations = __salt__['mc_locations.settings']()
        fqdn = grains['id']
        mumbleData = __salt__['mc_utils.defaults'](
            'makina-states.services.sound.mumble', {
                'default': {
                    'use_caps': 0,
                    'start': 1,
                    'nofile': 16384,
                },
                'murmur': {
                    'supassword': htpassword,
                    'uname': 'mumble-server',
                    'password': '',
                    'sendversion': 'True',
                    'allowhtml': 'True',
                    'port': 64738,
                    'ice': 'tcp -h 127.0.0.1 -p 6502',
                    'textmessagelength': 0,
                    'imagemessagelength': 0,
                },
            }
        )
        __salt__['mc_macros.update_local_registry'](
            'mumble', local_conf, registry_format='pack')
        return mumbleData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
