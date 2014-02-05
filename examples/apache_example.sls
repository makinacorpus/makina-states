{# This file is an example of makina-states.services.http.apache usage
# how to:
#   - extend base states
#   - manage virtualhosts
#   - add or remove modules
#   - define your pillar based project custom values, default values, and overrides main defaults
#
# @see also the pillar.sample file
#
# Remember theses 4 rules for extend:
#  - 1: Always include the SLS being extended with an include declaration
#  - 2: Requisites (watch and require) are appended to, everything else is overwritten
#       Anyway, you can repeat require/watch parts, explicit is better than implicit
#  - 3: include & extend directives can be used only once per SLS file
#  - 4: You can override any ID you want inside the  extend declaration
#}
{% import 'makina-states/_macros/services.jinja' as services with context %}
{% set apache = services.apache %}
extend:
  makina-apache-main-conf:
    mc_apache:
      - version: "{{ salt['pillar.get']('project-foo-apache-version', '2.4') }}"
      - mpm: "{{ salt['pillar.get']('project-foo-apache-mpm', 'worker') }}"
  makina-apache-settings:
    file:
      - context:
        KeepAliveTimeout: "{{ salt['pillar.get']('project-foo-apache-KeepAliveTimeout', '3') }}"
        worker_StartServers: "{{ salt['pillar.get']('project-foo-apache-StartServers', '5') }}"
        worker_MinSpareThreads: "{{ salt['pillar.get']('project-foo-apache-MinSpareThreads', '60') }}"
        worker_MaxSpareThreads: "{{ salt['pillar.get']('project-foo-apache-MaxSpareThreads', '120') }}"
        worker_ThreadLimit: "{{ salt['pillar.get']('project-foo-apache-ThreadLimit', '120') }}"
        worker_ThreadsPerChild: "{{ salt['pillar.get']('project-foo-apache-ThreadsPerChild', '60') }}"
        worker_MaxRequestsPerChild: "{{ salt['pillar.get']('project-foo-apache-MaxRequestsPerChild', '1000') }}"
        worker_MaxClients: "{{ salt['pillar.get']('project-foo-apache-MaxClients', '500') }}"

{# Adding modules #}
my-apache-other-module--other-module-excluded:
  mc_apache.exclude_module:
    - modules:
      - proxy_http
      - proxy_html
      - rewrite
    - require_in:
      - mc_apache: makina-apache-main-conf

{# Removing modules #}
my-apache-other-module-included2:
  mc_apache.include_module:
    - modules:
      - authn_file
    - require_in:
      - mc_apache: makina-apache-main-conf
