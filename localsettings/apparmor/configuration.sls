include:
  - makina-states.localsettings.apparmor.hooks
{% set settings = salt['mc_apparmor.settings']() %}

{% for f, fdata in settings.confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
apparmor-conf-{{f}}:
  file.managed:
    - name: "{{fdata.get('target', f)}}"
    - source: "{{fdata.get('source', 'salt://makina-states/files'+f)}}"
    - mode: "{{fdata.get('mode', 750)}}"
    - user: "{{fdata.get('user', 'root')}}"
    - group:  "{{fdata.get('group', 'root')}}"
    {% if fdata.get('makedirs', True) %}
    - makedirs: true
    {% endif %}
    {% if template %}
    - template: "{{template}}"
    {%endif%}
    - watch:
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post
{% endfor %}

# apply ntp patch if needed
# applying a patch rather than a complete file to ensure that evolutions of the
# profile will be spotted
apparmor-ntp-patch:
  file.managed:
    - source: salt://makina-states/files/etc/apparmor.d/usr.sbin.ntpd.patch
    - name: /tmp/apparmor.patch
    - onlyif: |
              set -e
              test -e /etc/apparmor.d/usr.sbin.ntpd
              grep -q attach_disconnected /etc/apparmor.d/usr.sbin.ntpd && /bin/false
    - watch:
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post
  cmd.run:
    - name: cd / && patch -Np2 < /tmp/apparmor.patch
    - onlyif: |
              set -e
              test -e /etc/apparmor.d/usr.sbin.ntpd
              grep -q attach_disconnected /etc/apparmor.d/usr.sbin.ntpd && /bin/false
              test -e /tmp/apparmor.patch
    - watch:
      - file: apparmor-ntp-patch
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post

apparmor-ntp-patch2:
  file.managed:
    - source: salt://makina-states/files/etc/apparmor.d/usr.sbin.ntpd.perms.patch
    - name: /tmp/apparmor.patch2
    - onlyif: |
              set -e
              test -e /etc/apparmor.d/usr.sbin.ntpd
              egrep -q '/\\*\*/libopts\\*.so\\* r,' /etc/apparmor.d/usr.sbin.ntpd && /bin/false
    - watch:
      - cmd: apparmor-ntp-patch
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post
  cmd.run:
    - name: cd / && patch -Np2 < /tmp/apparmor.patch2
    - onlyif: |
              set -e
              test -e /etc/apparmor.d/usr.sbin.ntpd
              egrep -q '/\*\*/libopts\*.so\* r,' /etc/apparmor.d/usr.sbin.ntpd && /bin/false
              test -e /tmp/apparmor.patch2
    - watch:
      - file: apparmor-ntp-patch2
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post

{% macro restart(suf='') %}
ms-apparmor-restart{{suf}}:
{% if settings.get('enabled', True) %}
  service.running:
    - enable: true
{%else %}
  service.dead:
    - enable: false
{%endif %}
    - name: apparmor
    - watch:
      - mc_proxy: ms-apparmor-cfg-post
    - watch_in:
      - mc_proxy: ms-apparmor-post
{% endmacro %}
{{restart()}}
