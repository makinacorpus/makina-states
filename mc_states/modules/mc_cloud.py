# -*- coding: utf-8 -*-

'''
.. _module_mc_cloud:

mc_cloud / cloud registries & functions
==============================================



'''

# Import salt libs
import os
import copy
import mc_states.api
import socket
import yaml
import logging

from mc_states.saltapi import six
from mc_states.modules.mc_pillar import PILLAR_TTL
import mc_states.saltapi
from salt.utils.odict import OrderedDict
from mc_states.saltapi import (
    IPRetrievalError, RRError, NoResultError, PillarError)

__name = 'cloud'
log = logging.getLogger(__name__)
PREFIX = 'makina-states.cloud'
_marker = object()


def proxy_command(**data):
    if not data:
        data = {}
    if not data.get('ssh_gateway'):
        return ''
    cmd = 'ProxyCommand ssh'
    if data.get('ssh_gateway_key'):
        cmd += ' -i {0}'.format(data['ssh_gateway_key'])
    if data.get('ssh_gateway_port'):
        cmd += ' -p {0}'.format(data['ssh_gateway_port'])
    if data.get('ssh_gateway_user'):
        cmd += ' -l {0}'.format(data['ssh_gateway_user'])
    cmd += ' {0}'.format(data['ssh_gateway'])
    cmd += ' nc %h %p'
    return cmd


def get_user():
    try:
        return os.getlogin()
    except OSError:
        return 'root'


def ssh_key_path(key='id_dsa', user='root', folder=None):
    homes = '/home'
    if folder is None:
        if user in ['root', 'toor']:
            folder = '/root/.ssh'
        else:
            folder = os.path.join(homes, user, '.ssh')
    return os.path.join(folder, key)


def ssh_settings(user=None,
                 ssh_name=None,
                 ssh_host=None,
                 ssh_port=22,
                 ssh_username='root',
                 ssh_sudo=None,
                 ssh_key=None,
                 ssh_password=None,
                 ssh_gateway=None,
                 ssh_gateway_port=22,
                 ssh_gateway_user='root',
                 ssh_gateway_key=_marker,
                 ssh_gateway_password=None):
    if ssh_host and not ssh_name:
        ssh_name = ssh_host
    if not user:
        user = get_user()
    if ssh_key and not ssh_key.startswith(os.path.sep):
        ssh_key = ssh_key_path(key=ssh_key, user=user)
    if ssh_gateway_key is _marker:
        ssh_gateway_key = ssh_key
    data = {'ssh_name': ssh_name,
            'ssh_host': ssh_host,
            'ssh_port': ssh_port,
            'ssh_username': ssh_username,
            'ssh_sudo': ssh_sudo,
            'ssh_key': ssh_key,
            'ssh_password': ssh_password,
            'ssh_gateway': ssh_gateway,
            'ssh_gateway_port': ssh_gateway_port,
            'ssh_gateway_user': 'root',
            'ssh_gateway_key': ssh_key,
            'ssh_gateway_password': ssh_gateway_password}
    return data


def ssh_host_settings(id_, **defaults):
    _s = __salt__
    db = _s['mc_pillar.get_db_infrastructure_maps']()
    ssh_hosts = _s['mc_pillar.get_ssh_hosts']()
    data = _s['mc_cloud.ssh_settings'](ssh_name=id_)
    if id_ in db['vms'] or id_ in db['bms']:
        try:
            ssh_host = _s['mc_pillar.ips_for'](id_)[0]
        except IPRetrievalError:
            ssh_host = id_
    defaults.setdefault('ssh_name', id_)
    defaults.setdefault('ssh_host', ssh_host)
    data = _s['mc_utils.dictupdate'](
        data,
        dict([(a, defaults[a]) for a in defaults
              if a in data]))
    data = _s['mc_utils.dictupdate'](
        data, copy.deepcopy(ssh_hosts.get(id_, {})))
    if id_ in db['vms']:
        try:
            tip = _s['mc_pillar.ips_for'](db['vms'][id_]['target'])[0]
        except IPRetrievalError:
            pass
        else:
            if tip == ssh_host:
                # vm is natted behind compute node, try to find out the port
                data['ssh_port'] = _s['mc_cloud_compute_node.get_ssh_port'](
                    id_, target=db['vms'][id_]['target'])
    if not data['ssh_host']:
        data['ssh_host'] = ssh_host
    return data


def exposed_ssh_settings(ttl=PILLAR_TTL):
    def _do():
        return __salt__['mc_utils.defaults'](
            mc_states.saltapi.SSH_CON_PREFIX, {})
    cache_key = __name + '.exposed_ssh_settings'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def default_settings():
    '''
    makina-states cloud global configuration options

    master
      The default master to link to into salt cloud profile
    master_port
      The default master port to link to into salt cloud profile
    pvdir
      salt cloud providers directory
    pfdir
      salt cloud profile directory
    bootsalt_branch
      bootsalt branch to use (default: master or prod if prod)
    bootsalt_args
      makina-states bootsalt args in salt mode
    keep_tmp
      keep tmp files
    ssh_gateway (all the gw params are opt.)
         ssh gateway info
    ssh_gateway_port
         ssh gateway info
    ssh_gateway_user
         ssh gateway info
    ssh_gateway_key
         ssh gateway info
    ssh_gateway_password
         ssh gateway info

    is
        mapping with various informations

        controller
            is this minion a cloud controller

        compute_node
            is this minion a cloud compute node

        vm
            is this minion a cloud operating vm

    '''
    msr = __salt__['mc_locations.msr']()
    pr = __salt__['mc_locations.first_pillar_root']()
    root = msr
    prefix = os.path.join(msr, 'etc')
    try:
        id_ = __grains__['id']
    except (TypeError, KeyError):
        id_ = __opts__['id']
    data = {
        'root': root,
        'all_pillar_dir': prefix + '/makina-states/cloud-controller',
        'ssl': {
            'cert_days': 365*1000,
            'ca': {
                'ca_name': id_,
                'bits': 2048,
                'days': 365*1000,
                'CN': 'makina-states-cloud-controller',
                'C': 'FR',
                'ST': 'PdL',
                'L': 'Nantes',
                'O': 'Makina Corpus',
                'OU': None,
                'emailAddress': 'contact@makina-corpus.com',
            }
        },
        'all_sls_dir': 'cloud-controller',
        'compute_node_sls_dir': (
            '{all_sls_dir}/controller'
        ),
        'compute_node_sls_dir': (
            '{all_sls_dir}/compute_node'
        ),
        'compute_node_pillar_dir': (
            '{all_pillar_dir}/compute_node'
        ),
        'ssl_dir': '{all_sls_dir}/ssl',
        'ssl_pillar_dir': '{all_pillar_dir}/ssl',
        'prefix': prefix,
        'script': msr+'/_scripts/boot-salt.sh',
        'bootstrap_shell': 'bash',
        'bootsalt_args': '-C --no-colors',
        'bootsalt_branch': 'v2',
        'pvdir': prefix + "/salt/cloud.providers.d",
        'pfdir': prefix + "/salt/cloud.profiles.d",
        # states registry settings
        'generic': True,
        'saltify': True,
        'lxc': False,
        'kvm': False,
        'is': {'compute_node': False,
               'vm': False,
               'controller': False},
        'lxc.defaults.backing': 'dir',
    }
    # retrocompat
    data.update(ssh_settings())
    return data


def extpillar_settings(id_=None, ttl=PILLAR_TTL, *args, **kw):
    '''
    return the cloud global configuation
    '''
    def _do(id_=None, limited=False):
        _s = __salt__
        _o = __opts__
        if id_ is None:
            id_ = _s['mc_pillar.minion_id']()
        conf = _s['mc_pillar.get_configuration'](
            _s['mc_pillar.minion_id']())
        extdata = _s['mc_pillar.get_global_clouf_conf']('cloud')
        mid = _s['mc_pillar.minion_id']()
        default_env = _s['mc_env.ext_pillar'](id_).get('env', '')
        default_port = 4506
        data = _s['mc_utils.dictupdate'](
            _s['mc_utils.dictupdate'](
                default_settings(), {
                    'ssl': {'ca': {'ca_name': id_}},
                    'master_port': _o.get('ret_port',
                                          _o.get('master_port', default_port)),
                    'master': mid,
                    # states registry settings
                    'generic': True,
                    'saltify': True,
                    'lxc': conf.get('cloud_control_lxc', True),
                    'kvm': conf.get('cloud_control_kvm', True)}
            ), extdata)
        if not data['bootsalt_branch']:
            data['bootsalt_branch'] = {'dev': 'master',
                                       'prod': 'v2',
                                       'preprod': 'v2'}.get(
                                           default_env, 'v2')
        data = _s['mc_utils.format_resolve'](data)
        return data
    limited = kw.get('limited', False)
    cache_key = 'mc_cloud.extpillar_settings{0}{1}'.format(id_, limited)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, limited], {}, cache_key, ttl)


def is_a_vm(id_=None, ttl=PILLAR_TTL):
    def _do(id_=None):
        if id_ is None:
            id_ = __grains__['id']
        _s = __salt__
        vms = _s['mc_cloud_compute_node.get_vms']()
        if id_ in vms:
            return True
        return False
    cache_key = 'mc_cloud.is_a_vm{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_a_compute_node(id_=None, ttl=PILLAR_TTL):
    def _do(id_=None):
        if id_ is None:
            id_ = __grains__['id']
        _s = __salt__
        targets = _s['mc_cloud_compute_node.get_targets']()
        if id_ in targets:
            return True
        return False
    cache_key = 'mc_cloud.is_a_compute_node{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_a_controller(id_=None, ttl=PILLAR_TTL):
    def _do(id_):
        if id_ is None:
            id_ = __grains__['id']
        _s = __salt__
        conf = _s['mc_pillar.get_configuration'](id_)
        if (
            (_s['mc_pillar.minion_id']() == id_)
            or conf.get('cloud_master', False)
        ):
            return True
        return False
    cache_key = 'mc_cloud.is_a_controller{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_a_cloud_member(id_=None):
    if id_ is None:
        id_ = __grains__['id']
    return any([is_a_vm(id_),
                is_a_compute_node(id_),
                is_a_controller(id_)])


def ssl_certs_for(main_domain, domains=None, ssl_certs=None):
    _s = __salt__
    if ssl_certs is None:
        ssl_certs = []
    if not isinstance(domains, list):
        domains = []
    domains = [a for a in domains]
    if main_domain not in domains:
        domains.insert(0, main_domain)
    domains = _s['mc_utils.uniquify'](domains)
    for domain in domains:
        for cert, key, chain in _s['mc_ssl.ca_ssl_certs'](domain):
            full = cert + chain + key
            try:
                certname = _s['mc_ssl.load_cert'](
                    _s['mc_ssl.ssl_chain'](domain, cert)[0]
                ).get_subject().CN
            except Exception:
                pass
            if certname not in [a[0] for a in ssl_certs]:
                ssl_certs.append((certname, full, cert, key, chain))
    return ssl_certs


def add_ms_ssl_certs(data, extdata=None):
    if not isinstance(extdata, dict):
        extdata = data
    for i in extdata.get('ssl_certs', []):
        __salt__['mc_pillar.add_ssl_cert'](
            i[0], i[2] + i[4], i[3], data=data)
    return data


def filter_exposed_data(target, data, mode='full'):
    data = copy.deepcopy(data)
    if mode != 'full':
        for k in [a for a in data]:
            if k in [target]:
                continue
            for l in ['pass', 'user']:
                if l in k:
                    data.pop(k, None)
    return data


def gather_expositions(ttl=PILLAR_TTL):
    '''
    Merge expositions amongst CN & VM settings
    as a vm can also be a compute node itself
    '''
    def _do():
        _s = __salt__
        data = OrderedDict()
        direct = data.setdefault('direct', OrderedDict())
        indirect = data.setdefault('indirect', OrderedDict())
        vms = _s['mc_cloud_compute_node.get_vms']()
        targets = _s['mc_cloud_compute_node.get_targets']()
        for vkind, fun, mapping in [
            ('vms',
             'mc_pillar.get_cloud_conf_for_vm',
             vms),
            ('cns',
             'mc_pillar.get_cloud_conf_for_cn',
             targets),
        ]:
            for i, tdata in six.iteritems(mapping):
                if _s['mc_cloud.is_a_compute_node'](i):
                    kind = 'cns'
                else:
                    kind = 'vms'
                if not (is_a_vm(i) or is_a_compute_node(i)):
                    continue
                rexpose = direct.setdefault(i, OrderedDict())
                indirect_rexpose = indirect.setdefault(i, OrderedDict())
                cdata = _s[fun](i)
                if not cdata or not isinstance(cdata, dict):
                    continue
                expose = cdata.setdefault('expose', [])
                expose_limited = cdata.setdefault(
                    'expose_limited', OrderedDict())
                exposed = cdata.setdefault('exposed', [])
                exposed_limited = cdata.setdefault(
                    'expose_limited_in', OrderedDict())
                if not isinstance(expose, list):
                    expose = []
                if not isinstance(expose_limited, dict):
                    expose_limited = OrderedDict()
                if not isinstance(exposed, list):
                    exposed = []
                if not isinstance(exposed_limited, dict):
                    exposed_limited = OrderedDict()
                if not (
                    expose or
                    expose_limited or
                    exposed or
                    exposed_limited
                ):
                    continue
                for e in expose:
                    expose_limited[e] = 'full'
                for e in exposed:
                    exposed_limited[e] = 'full'
                for exposure, fdict in [
                    (expose_limited, rexpose),
                    (exposed_limited, indirect_rexpose)
                ]:
                    for item, access in six.iteritems(exposure):
                        if _s['mc_cloud.is_a_compute_node'](item):
                            ikind = 'cns'
                        else:
                            ikind = 'vms'
                        dex = fdict.setdefault(
                            item, {'access': None, 'kinds': []})
                        if ikind not in dex['kinds']:
                            dex['kinds'].append(ikind)
                        # first level try wins, be sure to set
                        # it to be consistent amongst all declaration in conf !
                        if dex['access'] is None:
                            dex['access'] = access
        directs = [a for a in direct]
        indirects = [a for a in indirect]
        for lmaps, tmap, itmap in [
            (indirects, indirect, direct),
            (directs, direct, indirect),
        ]:
            for host in lmaps:
                mapped = tmap[host]
                for ohost, odata in mapped.items():
                    expose = itmap.setdefault(ohost, OrderedDict())
                    edata = expose.setdefault(
                        host,
                        {'access': None, 'kinds': []})
                    if edata['access'] is None:
                        edata['access'] = odata['access']
                    for kind in odata['kinds']:
                        if kind not in edata['kinds']:
                            edata['kinds'].append(kind)
        return data
    cache_key = '{0}.{1}'.format(__name, 'gather_expositions')
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def gather_exposed_data(target, ttl=PILLAR_TTL):
    def _do(target):
        _s = __salt__
        exposed_to_me = copy.deepcopy(
            gather_expositions()['indirect'].get(target, OrderedDict())
        )
        if target not in exposed_to_me:
            exposed_to_me[target] = {'access': 'full', 'kinds': []}
        kinds = exposed_to_me[target].setdefault('kinds', [])
        if is_a_vm(target):
            if 'vms' not in kinds:
                kinds.append('vms')
        if is_a_compute_node(target):
            if 'cns' not in kinds:
                kinds.append('cns')
        exposed_datas = OrderedDict()
        if not exposed_to_me:
            return {}
        for host, tdata in six.iteritems(exposed_to_me):
            for kind in tdata['kinds']:
                gepillar = copy.deepcopy(
                    ext_pillar(host, limited=True, prefixed=False))
                fun = {'vms': 'mc_cloud_vm.ext_pillar',
                       'cns': 'mc_cloud_compute_node.ext_pillar'}[kind]
                sepillar = copy.deepcopy(
                    _s[fun](host, prefixed=False, limited=True))
                gepillar = _s['mc_utils.dictupdate'](gepillar, sepillar)
                if kind == 'vms':
                    vms = gepillar.pop('vms', {})
                    gepillar.pop('vts', {})
                    vm = vms.get(host, {})
                    if vm:
                        gepillar = _s['mc_utils.dictupdate'](gepillar, vm)
                # only direct cloud settings
                to_remove = [k
                             for k in six.iterkeys(gepillar)
                             if (
                                 k.startswith('makina-states')
                                 or k in ['ssl', 'ssl_certs']
                             )]
                for k in to_remove:
                    gepillar.pop(k, None)
                kexposed_datas = exposed_datas.setdefault(kind, OrderedDict())
                kexposed_datas[host] = _s['mc_utils.dictupdate'](
                    kexposed_datas.setdefault(host, OrderedDict()),
                    filter_exposed_data(target, gepillar, tdata['access']))
        return exposed_datas
    cache_key = '{0}.{1}.{2}'.format(__name, 'gather_exposed_data', target)
    return __salt__['mc_utils.memoize_cache'](_do, [target], {}, cache_key, ttl)


def ext_pillar(id_, prefixed=True, ttl=PILLAR_TTL, *args, **kw):
    '''
    Makina-states cloud extpillar

    NOTE
        This ext pillar is responsible for taking care of exposing
        other nodes configuration to a particular node if
        we have configured this via the expose/expose_limited settings

    expose/exposed
        list of vm or compute nodes which will have full
        access to the vm infos in via ext_pillar

        - expose mean give access to other vm conf
        - exposed mean take acces on other vm conf

    expose_limited/exposed_limited
        dict of vm or compute nodes which will have access
        to the vm infos via the ext_pillar
        Here sensitive info may be filtered, for now,
        nothing is implememted and we give full for now.

        Levels are(only full is really implemented):

            full
                full access to conf
            light
                all conf but passwords or sensitive
            network
                network conf only

        example of pilar conf settings in database.yaml:

            cloud_vm_attrs:
              myvm:
                expose_limited:
                    other_vm0: full
                    other_vm1: network
                    other_vm2: password
                    mynode: full

            cloud_cn_attrs:
              mynode:
                expose_limited:
                    other_vm1: full
                    other_vm2: network
                    other_node: password

        This can be accessed client side via mc_cloud.settings/expositions

            salt-call mc_cloud.settings -> expositions / vms or cns


    '''
    def _do(id_, prefixed, limited):
        data = {}
        _s = __salt__
        # run that to aliment the cache
        _s['mc_pillar.minion_id']()
        extdata = extpillar_settings(id_, limited=limited)
        vms = _s['mc_cloud_compute_node.get_vms']()
        targets = _s['mc_cloud_compute_node.get_targets']()
        if is_a_vm(id_):
            extdata['is']['vm'] = True
            vmvt = vms[id_]['vt']
            extdata['is']['{0}_vm'.format(vmvt)] = True
            nodetype_vts = {'lxc': ['lxccontainer'],
                            'docker': ['dockercontainer'],
                            'kvm': ['kvm']}.get(vmvt, [])
            for nodetype_vt in nodetype_vts:
                spref = 'makina-states.nodetypes.is.{0}'.format(nodetype_vt)
                data[spref] = True
        if is_a_compute_node(id_):
            extdata['is']['compute_node'] = True
            for i in targets[id_]['vts']:
                extdata['is']['{0}_compute_node'.format(i)] = True
                extdata['is']['{0}_host'.format(i)] = True
                data['makina-states.services.virt.' + i] = True
            data['makina-states.services.is.proxy.haproxy'] = True
            data['makina-states.services.is.firewall.firewall'] = True
        if not limited:
            data[
                'makina-states.cloud.expositions'
            ] = gather_exposed_data(id_)
        if any([
            extdata['is']['vm'],
            extdata['is']['compute_node']
        ]):
            data.update(_s['mc_cloud_vm.ext_pillar'](
                id_, limited=limited))
        if any([
            extdata['is']['controller'],
            extdata['is']['compute_node']
        ]):
            data.update(_s['mc_cloud_compute_node.ext_pillar'](
                id_, limited=limited))
        if is_a_controller(id_):
            extdata['is']['controller'] = True
            data.update(_s['mc_cloud_saltify.ext_pillar'](
                id_, limited=limited))
        # if any of vm/computenode/controller
        # expose global cloud conf
        if any(extdata['is'].values()):
            data.update(_s['mc_cloud_controller.ext_pillar'](
                id_, limited=limited))
            data.update(_s['mc_cloud_images.ext_pillar'](
                id_, limited=limited))
            if prefixed:
                data[PREFIX] = extdata
            else:
                data = _s['mc_utils.dictupdate'](data, extdata)

        return data
    limited = kw.get('limited', False)
    cache_key = 'mc_cloud.ext_pillar{0}{1}{2}'.format(
        id_, prefixed, limited)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, prefixed, limited], {},
                         cache_key, ttl)


'''
On node side, after ext pillar is loaded
'''


def is_(typ, ttl=120):
    def do(typ):
        gr = 'makina-states.cloud.is.{0}'.format(typ)
        ret = __salt__['mc_utils.get'](gr, False)
        return ret
    cache_key = '{0}.{1}.{2}'.format(__name, 'is_', typ)
    return __salt__['mc_utils.memoize_cache'](do, [typ], {}, cache_key, ttl)


def is_vm():
    return is_('vm')


def is_compute_node():
    return is_('compute_node')


def is_lxc_compute_node():
    return is_('lxc_compute_node')


def is_controller():
    return is_('controller')


def metadata():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['services'])
    return _metadata()


def settings(ttl=60):
    '''
    Global cloud configuration
    '''
    def _do():
        _s = __salt__
        _g = __grains__
        _o = __opts__
        ct_registry = _s['mc_controllers.registry']()
        salt_settings = _s['mc_salt.settings']()
        root = salt_settings['salt_root']
        prefix = __opts__['config_dir']
        #    fic.write(pformat(__opts__))
        data = _s['mc_utils.defaults'](
            'makina-states.cloud',
            _s['mc_utils.dictupdate'](
                default_settings(), {
                    'expositions': {'vms': {}, 'cns': {}},
                    'root': root,
                    'all_pillar_dir': (
                        os.path.join(
                            _o['pillar_roots']['base'][0],
                            'cloud-controller')),
                    'ssl': {'ca': {'ca_name': _s[
                        'mc_pillar.minion_id']()}},
                    'prefix': prefix,
                    'pvdir': prefix + "/cloud.providers.d",
                    'pfdir': prefix + "/cloud.profiles.d",
                }))
        if not data['bootsalt_branch']:
            data['bootsalt_branch'] = {
                'prod': 'v2',
                'preprod': 'v2',
            }.get(_s['mc_env.settings']()['default_env'], None)
        if not data['bootsalt_branch']:
            data['bootsalt_branch'] = 'master'
        return data
    cache_key = '{0}.{1}'.format(__name, 'settings')
    data = __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)
    return data


def registry():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'generic': {'active': False},
            'lxc': {'active': False},
            'kvm': {'active': False},
            'saltify': {'active': False}})
    return _registry()


def get_cloud_settings():
    _s = __salt__
    from_extpillar = not _s['mc_pillar.loaded']()
    if from_extpillar:
        reg = _s['mc_controllers.registry']()
        if (
            not _s['mc_pillar.has_db']()
        ):
            from_extpillar = False
    if from_extpillar:
        cloudSettings = _s['mc_cloud.extpillar_settings']()
    else:
        import pdb;pdb.set_trace()  ## Breakpoint ##
        cloudSettings = _s['mc_cloud.settings']()
    return cloudSettings
