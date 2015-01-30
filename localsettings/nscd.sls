{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nscd.rst
#}
{{ salt['mc_macros.register']('localsettings', 'nscd') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}
nscd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - nscd

nscd-restart:
  cmd.run:
    - name: |
            if [ -f /usr/sbin/service ];then
              service nscd restart
            else
              /etc/init.d/nscd restart
            fi
    - require:
      - pkg: nscd-pkgs
    - watch_in:
      - mc_proxy: nscd-end-hook
touch-etc-nsswitch-conf:
  file.touch:
    - name: {{ locs.conf_dir }}/nsswitch.conf
{% if nscd.service_enabled %}
nscd:
  service.running:
    - enable: True
    - require:
      - cmd: nscd-restart
    - watch:
      - pkg: nscd-pkgs
      - file: touch-etc-nsswitch-conf
    - watch_in:
      - mc_proxy: nscd-end-hook
{% else %}
nscd-e:
  service.dead:
    - names:
      - nscd
    - enable: False
    - watch:
      - pkg: nscd-pkgs
      - file: touch-etc-nsswitch-conf
    - watch_in:
      - mc_proxy: nscd-end-hook
nscd:
  service.disabled:
    - names:
      - shorewall
      - shorewall6
    - watch:
      - pkg: nscd-pkgs
      - file: touch-etc-nsswitch-conf
    - watch_in:
      - mc_proxy: nscd-end-hook
{% endif %}
{% endif %}

nscd-end-hook:
  mc_proxy.hook: []
