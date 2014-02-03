{# extra setup on a lxc container #}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'lxccontainer') }}

{% if full %}
include:
  - makina-states.localsettings.pkgs
  - makina-states.nodetypes.vm
{% endif %}

# be sure to have all grains
{{localsettings.funcs.dummy('makina-lxc-proxy-dep') }}
# no require_in as in bootstrap time we may not have yet rendered the lxc bits

# lxc container
{% if salt['mc_utils.get']('makina-states.lxc', False) -%}
lxc-container-pkgs:
  pkg.installed:
    - pkgs:
      - apt-utils
    - require_in:
      - mc_proxy: makina-lxc-proxy-dep

makina-mark-as-lxc:
  cmd.run:
    - name: echo lxc > /run/container_type
    - unless: grep -q lxc /run/container_type
    - requires:
      - mc_proxy: makina-lxc-proxy-dep

etc-init-lxc-setup:
  file.managed:
    - name: /etc/init/lxc-setup.conf
    - source: salt://makina-states/files/etc/init/lxc-setup.conf
    - user: root
    - group: root
    - mode: 0755
    - requires:
      - cmd: makina-mark-as-lxc

etc-init-lxc-stop:
  file.managed:
    - name: /etc/init/lxc-stop.conf
    - source: salt://makina-states/files/etc/init/lxc-stop.conf
    - user: root
    - group: root
    - mode: 0755
    - requires:
      - cmd: makina-mark-as-lxc

lxc-cleanup:
  file.managed:
    - name: /sbin/lxc-cleanup.sh
    - source: salt://makina-states/files/sbin/lxc-cleanup.sh
    - user: root
    - group: root
    - mode: 0755

lxc-install-non-harmful-packages:
  cmd.script:
    - source: salt://makina-states/_scripts/build_lxccorepackages.sh
    - requires:
      - mc_proxy: makina-lxc-proxy-dep
      - cmd: makina-mark-as-lxc
      - file: lxc-cleanup
    {% if full %}
    - require_in:
      - pkg: ubuntu-pkgs
      - pkg: sys-pkgs
    {% endif %}

do-lxc-cleanup:
  cmd.run:
    - name: /sbin/lxc-cleanup.sh
    - requires:
      - file: lxc-cleanup
      - mc_proxy: makina-lxc-proxy-dep
      - cmd: lxc-install-non-harmful-packages
      {% if full %}
      - pkg: ubuntu-pkgs
      - pkg: sys-pkgs
      - pkg: net-pkgs
      - pkg: dev-pkgs
      {% endif %}
{% endmacro %}
{{do(full=False)}}
