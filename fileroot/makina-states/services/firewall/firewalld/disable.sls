{% import "makina-states/_macros/h.jinja" as h with context %}
include:
  - makina-states.services.firewall.firewalld.hooks
  - makina-states.services.firewall.firewall.hooks
  - makina-states.services.firewall.firewalld.unregister
  - makina-states.services.firewall.firewall.configuration
firewalld-disable-makinastates-firewalld:
  file.absent:
    - names:
      - /etc/apt/sources.list.d/firewalld.list
    - watch:
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable

{% macro after_macro() %}
    - watch:
      - file: firewalld-disable-makinastates-firewalld
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
      - pkg: firewalld-purge-firewalld
{% endmacro %}
{% for i in ['firewalld'] %}
{{h.toggle_service(i, prefix='firewalld_disable', action='stop', after_fallback_macro=after_macro)}}
{% endfor %}
firewalld-purge-firewalld:
  pkg.purged:
    - pkgs: [firewalld]
    - watch:
      - file: firewalld-disable-makinastates-firewalld
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
firewalld-uninstall-firewalld:
  pkg.removed:
    - pkgs: [firewalld]
    - watch:
      - pkg: firewalld-purge-firewalld
      - file: firewalld-disable-makinastates-firewalld
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
