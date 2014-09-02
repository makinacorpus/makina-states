#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import salt libs
import mc_states.utils
import random
import os
import logging
import traceback


log = logging.getLogger(__name__)

__name = 'salt'


def get_global_conf(id_, gconf=None):
    if not gconf:
        gconf = __salt__['mc_pillar.get_configuration'](id_)
    return gconf


def get_mail_conf(id_, gconf=None):
    gconf = get_global_conf(id_, gconf)
    if not gconf['manage_mails']:
        return {}
    data = {}
    mail_conf = __salt__['mc_pillar.get_mail_configuration'](id_)
    dest = mail_conf['default_dest'].format(id=id_)
    data['makina-states.services.mail.postfix'] = True
    data['makina-states.services.mail.postfix.mode'] = mail_conf['mode']
    if mail_conf.get('transports'):
        transports = data.setdefault(
            'makina-states.services.mail.postfix.transport', [])
        for entry, host in mail_conf['transports'].items():
            if entry != '*':
                transports.append({
                    'transport': entry,
                    'nexthop': 'relay:[{0}]'.format(host)})
            if '*' in mail_conf['transports']:
                transports.append(
                    {'nexthop':
                     'relay:[{0}]'.format(mail_conf['transports']['*'])})
        if mail_conf['auth']:
            passwds = data.setdefault(
                'makina-states.services.mail.postfix.sasl_passwd', [])
            data['makina-states.services.mail.postfix.auth'] = True
            for entry, host in mail_conf['smtp_auth'].items():
                passwds.append({
                    'entry': '[{0}]'.format(entry),
                    'user': host['user'],
                    'password': host['password']})
        if mail_conf.get('virtual_map'):
            vmap = data.setdefault(
                'makina-states.services.mail.postfix.virtual_map', {})
        for record in mail_conf['virtual_map']:
            for item, val in record.items():
                vmap[item.format(id=id_, dest=dest)] = val.format(
                    id=id_, dest=dest)
    return data


def ext_pillar(id_, pillar, *args, **kw):
    data = {}
    gconf = get_global_conf(id_)
    for callback in [
        get_mail_conf
    ]:
        args, kw = (id_,), {'gconf': gconf}
        try:
            data = __salt__['mc_utils.dictupdate'](data,
                                                   callback(*args, **kw))
        except Exception, ex:
            trace = traceback.format_exc()
            log.error('ERROR in mc_pillar {0}'.format(callback))
            log.error(ex)
            log.error(trace)
    return data

# vim:set et sts=4 ts=4 tw=80:
