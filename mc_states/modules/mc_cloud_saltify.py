# -*- coding: utf-8 -*-
'''
.. _module_mc_cloud_saltify:

mc_cloud_saltify / cloud related variables
==============================================



- This contains generate settings around cloud_saltify
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_lxc`.

'''
# Import salt libs
import copy
import mc_states.api
from pprint import pformat
from salt.utils.odict import OrderedDict
from mc_states import saltapi
from mc_states.modules.mc_pillar import PILLAR_TTL

__name = 'cloud_saltify'
VT = 'saltify'
PREFIX = 'makina-states.cloud.{0}'.format(VT)


def gen_id(name):
    return name.replace('.', '-')


def default_settings(cloudSettings):
    """
    Except targets, we take all the default from
    :ref:`module_mc_cloud`

    bootsalt_args
        args to give to bootsalt
        (default to cloudcontroller configured value)
    master
        salt master fqdn to rattach to
        (default to cloudcontroller configured value)
    master_port
        salt master port to rattach to
        (default to cloudcontroller configured value)
    bootsalt_branch
        default bootsalt_branch to use
        (default to cloudcontroller configured value)
    id
        fqdn/minionid of the host to saltify
    ssh_gateway
        (all the gw params are opt.)
        ssh gateway info
    ssh_gateway_port
        ssh gateway info
    ssh_gateway_user
        ssh gateway info
    ssh_gateway_key
        ssh gateway info and default hosts key to ssh in
    ssh_gateway_password
        ssh gateway password

    ssh_keyfile
        use the ssh key (private) instead of using password base
        authentication
    name
        name of the host if it does not match id
        (do not use...)
    ip
        eventual ip if dns is not yet accessible
    ssh_username
        user name to connect as to provision the box
    password
        password to use (leave empty for key)
    no_sudo_password
        disable sudo password handling (default: False).
        If the guest system disable sudo password asking, set this
        parameter to true
    sudo_password
        sudo_password (leave empty to default to password)
    sudo
        do we use sudo (bool)
    targets
        List of minionid Targets where to bootstrap salt using the saltcloud
        saltify driver (something accessible via ssh)
    """
    data = {'script_args': cloudSettings['bootsalt_args'],
            'ssh_gateway': cloudSettings['ssh_gateway'],
            'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
            'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
            'ssh_gateway_password': cloudSettings['ssh_gateway_password'],
            'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
            'ssh_username': 'root',
            'ssh_keyfile': None,
            'master': cloudSettings['master'],
            'no_sudo_password': False,
            'keep_tmp': False,
            'master_port': cloudSettings['master_port'],
            'bootsalt_branch': cloudSettings['bootsalt_branch'],
            'password': None,
            'sudo_password': None,
            'no_sudo_password': None,
            'targets': OrderedDict()}
    return copy.deepcopy(data)


def target_extpillar(name, c_data=None, ttl=PILLAR_TTL):
    '''
    Settings for bootstrapping a target using saltcloud saltify
    driver (something accessible via ssh)
    mappings in the form:

    '''
    def _do(name, c_data):
        _s = __salt__
        if c_data is None:
            c_data =  OrderedDict([
                ('password', _s['mc_pillar.get_passwords'](
                    name
                )['clear']['root']),
                ('ssh_username', 'root')])
        sdata = default_settings(_s['mc_cloud.extpillar_settings']())
        del sdata['targets']
        branch = c_data.get('bootsalt_branch', sdata['bootsalt_branch'])
        defaults = OrderedDict()
        name = c_data.get('name', name)
        defaults.update({'name': name,
                         'id': name,
                         'profile': 'ms-salt-minion',
                         'ssh_host': c_data.get('ip', name)})
        c_data = _s['mc_utils.dictupdate'](
            _s['mc_utils.dictupdate'](sdata, c_data), defaults)
        c_data = saltapi.complete_gateway(c_data, sdata)
        if (
            ('-b' not in c_data['script_args'])
            and ('--branch' not in c_data['script_args'])
        ):
            defaults['script_args'] = (
                c_data['script_args'] + ' -b {0}'.format(branch))

        if (
            not c_data['ssh_keyfile']
            and not c_data['password']
            and sdata['ssh_gateway_key']
        ):
            c_data['ssh_keyfile'] = sdata['ssh_gateway_key']
        if c_data['ssh_keyfile'] and c_data['password']:
            raise ValueError('Not possible to have sshkey + password '
                             'for \n{0}'.format(pformat(c_data)))
        if not c_data['ssh_keyfile'] and not c_data['password']:
            raise ValueError('We should either have one of sshkey + '
                             'password for \n{0}'.format(pformat(c_data)))
        sudo_password = c_data['sudo_password']
        if not sudo_password:
            sudo_password = c_data['password']
        if c_data['no_sudo_password']:
            sudo_password = None
        c_data['sudo_password'] = sudo_password
        v = 'saltify'
        c_data = _s['mc_utils.dictupdate'](
            c_data, _s['mc_pillar.get_global_clouf_conf'](v))
        c_data = _s['mc_utils.dictupdate'](
            c_data, _s['mc_pillar.get_cloud_conf_for_cn'](name).get(v, {}))
        return c_data
    cache_key = '{0}.{1}'.format(PREFIX, name)
    return __salt__['mc_utils.memoize_cache'](_do, [name, c_data], {}, cache_key, ttl)


def _add_host(_s, done_hosts, rdata, host):
    done_hosts.append(host)
    rdata[host] = target_extpillar(host)


def ext_pillar(id_, prefixed=True, ttl=PILLAR_TTL, *args, **kw):
    def _do(id_, prefixed):
        _s = __salt__
        rdata = {}
        supported_vts = _s['mc_cloud_compute_node.get_vts']()
        done_hosts = []
        ivars = _s['mc_pillar.get_db_infrastructure_maps']()
        nmh = _s['mc_pillar.query']('non_managed_hosts', {})
        for vt, targets in _s['mc_pillar.query']('vms').items():
            if vt not in supported_vts:
                continue
            for host, vms in targets.items():
                if any([
                    (host in done_hosts),
                    (host in nmh)
                ]):
                    continue
                _add_host(_s, done_hosts, rdata, host)
        for host, data in ivars['standalone_hosts'].items():
            if any([(host in done_hosts), (host in nmh)]):
                continue
            _add_host(_s, done_hosts, rdata, host)
            for k, val in data.items():
                if val and val not in ['ssh_username']:
                    rdata[host][k] = val
        data = default_settings(_s['mc_cloud.extpillar_settings']())
        data['targets'] = rdata
        if not _s['mc_cloud.is_a_controller'](id_):
            if id_ in data['targets']:
                for i in [a for a in data['targets'] if a != id_]:
                    data['targets'].pop(i, None)
            else:
                return {}
        if prefixed:
            data = {PREFIX: data}
        return data
    cache_key = '{0}.ext_pillar{1}{2}'.format(PREFIX, id_, prefixed)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, prefixed], {}, cache_key, ttl)


'''
Methods usable
After the pillar has loaded, on the compute node itself
'''


def settings(ttl=30):
    def _do():
        _s = __salt__
        cloudSettings = _s['mc_cloud.settings']()
        settings = _s['mc_utils.defaults'](PREFIX,
                                           default_settings(cloudSettings))
        return settings
    cache_key = '{0}.{1}'.format(PREFIX, 'settings')
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def target_settings(id_=None, ttl=30):
    def _do(id_):
        if id_ is None:
            id_ = __grains__['id']
        return settings()['targets'].get(id_, {})
    cache_key = '{0}.{1}.{2}'.format(PREFIX, 'target_settings', id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)
# vim:set et sts=4 ts=4 tw=80:
