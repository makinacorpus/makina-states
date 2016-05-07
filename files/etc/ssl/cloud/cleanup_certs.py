#!/usr/bin/env python
exit 0
{#
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import sys
# {% set settings = salt['mc_ssl.settings']() %}
# {% set certs = [] %}
# {% for scerts in [settings.get('certificatess', {}),
#                   settings.get('cas', {})] %}
# {% for did, cert in six.iteritems(scerts) %}
# {% do certs.append(cert) %}
# {% endfor %}
# {% endfor %}
state = "no"
certs = set()
for cert_dir in [
    d for d in [
        '{{settings.config_dir}}/certs',
        '{{settings.config_dir}}/separate',
        '{{settings.config_dir}}/trust',
    ] if os.path.exists(d)
]:
    [certs.add(os.path.join(cert_dir, a))
     for a in os.listdir(cert_dir)
     if (
        os.path.isfile(os.path.join(cert_dir, a)) and
        # if we do not have at lease one cert maching
        not any([a.startswith(prefix) for prefix in {{certs}}])
    )]
for fa in certs:
    if os.path.exists(fa):
        print("Removing stale {0}".format(fa))
        try:
            os.unlink(fa)
        except (OSError, IOError):
            continue
        else:
            state = "yes"
print("changed={0}".format(state))
# vim:set et sts=4 ts=4 tw=80:
#}
