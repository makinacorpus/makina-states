# -*- coding: utf-8 -*-
'''
.. _module_mc_apparmor:

mc_apparmor / apparmor functions
==================================
'''

# Import python libs
import logging
import mc_states.api

__name = 'apparmor'

log = logging.getLogger(__name__)


def settings():
    '''
    apparmor settings
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        confs = {}
        _g = __grains__
        enabled = (
            __salt__['mc_localsettings.apparmor_en']() and
            not __salt__['mc_nodetypes.is_container']())
        if _g['os'] in ['Ubuntu']:
            # if _g['osrelease'] < '15.04':
            #     pass
            confs.update({
                '/etc/apparmor.d/abstractions/lxc/powercontainer-base': {},
                '/etc/apparmor.d/abstractions/dockercontainer': {},
                # in fact this does not play nice with apparmor 2.8
                # which is the one we have on trusty(14.04)
                # '/etc/apparmor.d/abstractions/dbus': {},
                # '/etc/apparmor.d/abstractions/dbus-accessibility': {},
                # '/etc/apparmor.d/abstractions/dbus-accessibility-strict': {},
                # '/etc/apparmor.d/abstractions/dbus-session': {},
                # '/etc/apparmor.d/abstractions/dbus-session-strict': {},
                # '/etc/apparmor.d/abstractions/dbus-strict': {},
                # '/etc/apparmor.d/abstractions/libvirt-qemu': {},
                # '/etc/apparmor.d/abstractions/dbus-session-strict': {},
                # '/etc/apparmor.d/abstractions/base': {},
                # '/etc/apparmor.d/abstractions/lxc/container-base': {},
                # '/etc/apparmor.d/abstractions/lxc/start-container': {},
                # '/etc/apparmor.d/lxc/lxc-default': {},
                # '/etc/apparmor.d/lxc/lxc-default-with-mounting': {},
                # '/etc/apparmor.d/lxc/lxc-default-with-nesting': {},
                # '/etc/apparmor.d/lxc-containers': {},
                # '/etc/apparmor.d/usr.bin.lxc-start': {},
                # '/etc/apparmor.d/usr.lib.libvirt.virt-aa-helper': {},
                # '/etc/apparmor.d/usr.sbin.libvirtd': {},
                # '/etc/apparmor.d/usr.sbin.named': {},
                # '/etc/apparmor.d/usr.sbin.ntpd': {},
                # '/etc/apparmor.d/sbin.dhclient': {},
                # '/etc/apparmor.d/usr.sbin.rsyslogd': {},
                # '/etc/apparmor.d/usr.sbin.slapd': {},
                # '/etc/apparmor.d/usr.sbin.tcpdump': {}
            })
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.apparmor', {
                'enabled': enabled,
                'confs': confs})
        return data
    return _settings()
