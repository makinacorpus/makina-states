{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'dockercontainer') }}
{# only really do if docker or lxc, because destructive #}
{% if salt['mc_nodetypes.is_container']() %}
include:
  {% if full %}
  - makina-states.localsettings.pkgs.basepackages
  {% endif %}
  - makina-states.nodetypes.container
makina-mark-as-lxc:
  cmd.run:
    - name: echo docker > /run/container_type
    - unless: grep -q docker /run/container_type
    - watch:
      - mc_proxy: makina-lxc-proxy-mark
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cleanup
{% endif %}
{% endmacro %}
{{do(full=False)}}
