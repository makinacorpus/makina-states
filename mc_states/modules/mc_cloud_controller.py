# -*- coding: utf-8 -*-
'''
.. _module_mc_cloud_controller:

mc_cloud_controller / cloud related variables
==============================================

- This contains generate settings around salt_cloud
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_cloud_lxc`.

'''
# Import salt libs
from copy import deepcopy
from salt.utils.odict import OrderedDict
import mc_states.utils

__name = 'mc_cloud_controller'

# _TYPES = {
#     'saltify_nodes': {'conf_key': 'targets',
#                       'type': 'saltify',
#                       'data': _SALTIFY_NODES_METADATA},
#     'compute_nodes': {'conf_key': 'targets',
#                       'type': 'compute_node',
#                       'data': _COMPUTE_NODES_TYPES_METADATA},
#     'vms': {'conf_key': 'vms',
#             'type': 'vm',
#             'data': _VM_TYPES_METADATA},
# }
# _DEFAULT_METADATA = {
#     'name': None,
#     'vt_types': [],
#     'cn_types': [],
#     'reverse_proxy': False,
#     'firewall': False,
#     'activated': OrderedDict(),
# }
#
#


def gen_id(name):
    return name.replace('.', '-')


# def _register_compute_node(compute_datas, data):
#     pass
#
#
# def _register_vm(compute_datas, data):
#     pass
#
#
# def _register_saltified(compute_datas, data):
#     pass
#
#
# def _register_default_settings_for(compute_datas):
#     for typ_, typ_data in _TYPES.iteritems():
#         vsettings = __salt__['mc_cloud_{0}.settings'.format(typ_data['type'])]()
#         compute_data = compute_datas
#         compute_data.setdefault(target, deepcopy(_DEFAULT_METADATA))
#         for target, target_data in vsettings[vdata['conf_key'].iteritems():
#             mdata = compute_data[target]
#             mdata['name'] = target
#             if vt_data['conf_key'] == 'targets':
#                 mdata['reverse_proxy'] = True
#                 mdata['firewall'] = True
#     for vttype, vt_data in _VT_TYPES.iteritems():
#         for target, hosts in virtSettings[
#             vt_data['conf_key']
#         ].iteritems():
#             if not vttype in mdata['vt_types']:
#                 mdata['vt_types'].append(vttype)
#
#             if not gvttype in mdata['gvt_types']:
#                 mdata['gvt_types'].append(gvttype)
#             mdata['activated'][vttype] = True
#     return compute_data

def settings():
    """
    controller node settings
    """
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        #compute_data = OrderedDict()
        #compute_data = _register_default_settings_for(compute_data)
        data = __salt__['mc_utils.defaults'](
            'makina-states.cloud.controller', {
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
