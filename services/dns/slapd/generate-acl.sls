{% set settings = salt['mc_slapd.settings']() %}
include:
  - makina-states.services.dns.slapd.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set aclf = settings.SLAPD_CONF + "/cn=config/olcDatabase={-1}frontend.ldif" %}
gen-slapd-d-acls-schema:
  file.managed:
    - name: /etc/ldap/generate-acls.py
    - contents: |
                #!/usr/bin/env python
                from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
                import os
                import sys
                import json
                import ldif
                gldif = {'objectClass': ['olcDatabaseConfig',
                                  'olcFrontendConfig'],
                        'olcDatabase': ['{-1}frontend'],
                        'olcAccess': [
                          {% for a in settings.acls %}
                          """{{a}}""",
                          {% endfor %}
                        ],
                        'olcAddContentAcl': ['FALSE'],
                        'olcLastMod': ['TRUE'],
                        'olcMaxDerefDepth': ['0'],
                        'olcReadOnly': ['FALSE'],
                        'olcSchemaDN': ['cn=Subschema'],
                        'olcSizeLimit': ['5000'],
                        'olcSyncUseSubentry': ['FALSE'],
                        'olcMonitoring': ['FALSE'],
                        'structuralObjectClass': ['olcDatabaseConfig'],
                        'entryUUID': ['b2d27176-6a4f-1033-86d6-773bdb858bca'],
                        'creatorsName': ['cn=config'],
                        'createTimestamp': ["20140507165431Z"],
                        'modifyTimestamp': ["20140507165431Z"],
                        'entryCSN': ['20140507165431.978200Z#000000#000#000000'],
                        'modifiersName': ['cn=admin,cn=config'],
                }
                dn = 'olcDatabase={-1}frontend'
                ldif_writer = ldif.LDIFWriter(sys.stdout)
                ldif_writer.unparse(dn, gldif)
    - makedirs: true
    - mode: 700
    - user: {{settings.user}}
    - group: {{settings.user}}
slapd-d-acls-schema:
  file.managed:
    - name: /etc/ldap/apply-acls.sh
    - contents: |
                #!/usr/bin/env bash
                /etc/ldap/generate-acls.py > "{{aclf}}.new"
                if [ "x${?}" != "x0" ];then
                  exit 1
                fi
                if [ -f "{{aclf}}" ];then
                if [ "x$(diff -q "{{aclf}}.new" "{{aclf}}";echo ${?})" != "x0" ];then
                  echo 'changed="true"'
                else
                  echo 'changed="false"'
                fi
                fi
                cp -f "{{aclf}}.new" "{{aclf}}"
                rm -f "{{aclf}}.new"
    - makedirs: true
    - mode: 700
    - user: {{settings.user}}
    - group: {{settings.user}}
  cmd.run:
    - stateful: true
    - name: /etc/ldap/apply-acls.sh
    - watch:
      - file: slapd-d-acls-schema
      - file: gen-slapd-d-acls-schema
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endif %}
