#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
{% if certs.strip() %}
{% set certs = salt['mc_utils.json_load'](certs) %}
{% else%}
{% set certs = [] %}
{% endif%}
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import os
import sys
if os.path.exists('/etc/ssl/cloud/certs'):
    os.chdir('/etc/ssl/cloud/certs')
    certs = os.listdir('.')
    for a in certs:
        fa = os.path.join(os.getcwd(), a)
        if fa not in {{certs}}:
            print("Removing stale {0}".format(fa))
            os.unlink(fa)
os.unlink('{{f}}')
{#
#if os.path.exists('/etc/ssl/cloud/separate'):
#  sinfos = {{sacerts}} + {{socerts}} + {{skeys}} + {{sfcerts}} + {{sbcerts}}
#  os.chdir('/etc/ssl/cloud/separate')
#  certs = os.listdir('.')
#  [os.unlink(a) for a in certs if a not in sinfos] #}
#}
# vim:set et sts=4 ts=4 tw=80:
