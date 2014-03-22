{#
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/lxccontainer.rst
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}

{% set localsettings = nodetypes.localsettings %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'lxccontainer') }}

include:
  {% if full %}
  - makina-states.localsettings.pkgs
  {% endif %}
  - makina-states.localsettings.pkgs-hooks
  - makina-states.nodetypes.vm

makina-lxc-proxy-dep:
  mc_proxy.hook: []

# be sure to have all grains
# no require_in as in bootstrap time we may not have yet rendered the lxc bits

# lxc container
lxc-container-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - apt-utils
      - libfuse2
    - require_in:
      - mc_proxy: makina-lxc-proxy-dep

makina-mark-as-lxc:
  cmd.run:
    - name: echo lxc > /run/container_type
    - unless: grep -q lxc /run/container_type
    - require:
      - mc_proxy: makina-lxc-proxy-dep

etc-init-lxc-setup:
  file.managed:
    - name: /etc/init/lxc-setup.conf
    - source: salt://makina-states/files/etc/init/lxc-setup.conf
    - user: root
    - group: root
    - mode: 0755
    - require:
      - cmd: makina-mark-as-lxc

etc-init-lxc-stop:
  file.managed:
    - name: /etc/init/lxc-stop.conf
    - source: salt://makina-states/files/etc/init/lxc-stop.conf
    - user: root
    - group: root
    - mode: 0755
    - require:
      - cmd: makina-mark-as-lxc

lxc-cleanup:
  file.managed:
    - name: /sbin/lxc-cleanup.sh
    - source: salt://makina-states/files/sbin/lxc-cleanup.sh
    - user: root
    - group: root
    - mode: 0755

lxc-snap.sh:
  file.managed:
    - name: /sbin/lxc-snap.sh
    - source: salt://makina-states/files/sbin/lxc-snap.sh
    - user: root
    - group: root
    - mode: 0755

lxc-install-non-harmful-packages:
  file.managed:
    - source: salt://makina-states/_scripts/build_lxccorepackages.sh
    - name: /sbin/build_lxccorepackages.sh
    - user: root
    - group: root
    - mode: 750
    - require:
      - mc_proxy: makina-lxc-proxy-dep
      - cmd: makina-mark-as-lxc
      - file: lxc-cleanup
    - require_in:
      - mc_proxy: before-pkg-install-proxy
  cmd.run:
    - name: /sbin/build_lxccorepackages.sh
    - require:
      - mc_proxy: makina-lxc-proxy-dep
      - cmd: makina-mark-as-lxc
      - file: lxc-cleanup
      - file: lxc-install-non-harmful-packages
    - require_in:
      - mc_proxy: before-pkg-install-proxy

do-lxc-cleanup:
  cmd.run:
    - name: /sbin/lxc-cleanup.sh
    - require:
      - file: lxc-cleanup
      - cmd: lxc-install-non-harmful-packages
      - mc_proxy: makina-lxc-proxy-dep
      - mc_proxy: after-pkg-install-proxy

{% endmacro %}
{{do(full=False)}}
