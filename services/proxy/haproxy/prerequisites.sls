{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}

include:
  - makina-states.services.proxy.haproxy.hooks

haproxy-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - haproxy
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: haproxy-post-install-hook
