{% set settings = salt['mc_slapd.settings']() %}
include:
  - makina-states.services.dns.slapd.hooks
{#
removed and use now file.recurse with clean=true
slapd-d-cleanup-schema:
  file.managed:
    - name: /etc/ldap/cleanup-schema.py
    - contents: |
                #!/usr/bin/env python
                from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
                import os
                ldifs=[
                {% for a in settings.cn_config_files%}
                  '{{a}}',
                {%endfor%}
                  '{{settings.SLAPD_CONF}}/cn=config/olcDatabase={-1}frontend.ldif',
                ]
                ld = "{{settings.SLAPD_CONF}}"
                changed=False
                if os.path.isdir(ld):
                    for root, dirs, files in os.walk(ld):
                        for i in files:
                            pt = os.path.join(root, i)
                            if pt not in ldifs:
                                print("Removing {0}".format(pt))
                                os.remove(pt)
                                changed=True
                print("changed={0}".format(changed).lower())

    - makedirs: true
    - mode: 700
    - user: {{settings.user}}
    - group: {{settings.user}}
  cmd.run:
    - stateful: true
    - name: /etc/ldap/cleanup-schema.py
    - watch:
      - file: slapd-d-cleanup-schema
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
#}
