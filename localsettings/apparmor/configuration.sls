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
              if grep -q attach_disconnected /etc/apparmor.d/usr.sbin.ntpd;then exit 1;fi
    - watch:
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post
  cmd.run:
    - name: |
            set -e
            patch --dry-run -r- -Np2 < /tmp/apparmor.patch
            patch           -r- -Np2 < /tmp/apparmor.patch
    - cwd: /
    - onlyif: |
              set -e
              test -e /etc/apparmor.d/usr.sbin.ntpd
              if grep -q attach_disconnected /etc/apparmor.d/usr.sbin.ntpd;then exit 1;fi
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
              if egrep -q '/\*\*/libopts\*.so\* r,' /etc/apparmor.d/usr.sbin.ntpd;then exit 1;fi
    - watch:
      - cmd: apparmor-ntp-patch
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post
  cmd.run:
    - name: |
            set -e
            patch --dry-run -r- -Np2 < /tmp/apparmor.patch2 
            patch           -r- -Np2 < /tmp/apparmor.patch2
    - cwd: /
    - onlyif: |
              set -e
              test -e /etc/apparmor.d/usr.sbin.ntpd
              if egrep -q '/\*\*/libopts\*.so\* r,' /etc/apparmor.d/usr.sbin.ntpd;then exit 1;fi
              test -e /tmp/apparmor.patch2
    - watch:
      - file: apparmor-ntp-patch2
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post

{% macro restart(suf='') %}
{% if salt['mc_nodetypes.is_travis']() %}
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
{% endif %}
{% endmacro %}
{{restart()}}
