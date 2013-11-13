# This file is an example of makina-states.services.http usage 
# how to extend base states
# how to add virtualhosts
# how to add or remove modules
# how to define your pillar based project custom values, default values, and overrides main defaults
# @see also the pillar.sample file
#
## remember theses 4 rules for extend:
##1-Always include the SLS being extended with an include declaration
##2-Requisites (watch and require) are appended to, everything else is overwritten
##3-extend is a top level declaration, like an ID declaration, cannot be declared twice in a single SLS
##4-Many IDs can be extended under the extend declaration
include:
  - makina-states.services.http.apache
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

# Adding or removing modules
my-apache-other-module-included1:
  mc_apache.include_module:
    - modules:
      - proxy_http
      - proxy_html
    - require_in:
      - mc_apache: makina-apache-main-conf
# Adding or removing modules
my-apache-other-module-included2:
  mc_apache.include_module:
    - modules:
      - authn_file
    - require_in:
      - mc_apache: makina-apache-main-conf
my-apache-other-module--other-module-excluded:
  mc_apache.exclude_module:
    - modules:
      - rewrite
    - require_in:
      - mc_apache: makina-apache-main-conf

# Custom virtualhost
{% from 'makina-states/services/http/apache_defaults.jinja' import apacheData with context %}
{% from 'makina-states/services/http/apache_macros.jinja' import virtualhost with context %}
{{ virtualhost(apacheData = apacheData,
            site = "{{ salt['pillar.get']('project-foo-apache-vh1-name', 'www.foobar.com') }},
            small_name = "{{ salt['pillar.get']('project-foo-apache-vh1-nickname', 'foobar') }},
            active = True,
            number = '900',
            log_level = "{{ salt['pillar.get']('project-foo-apache-vh1-loglevel', 'debug') }},
            serverAlias = "{{ salt['pillar.get']('project-foo-apache-vh1-alias', 'foobar.com') }}",
            documentRoot = "{{ salt['pillar.get']('project-foo-apache-vh1-docroot', '/srv/projects/example/foobar/www') }}",
            redirect_aliases = True,
            allow_htaccess = False) }}
