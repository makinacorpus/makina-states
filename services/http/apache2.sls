# This file is an example of makina-states.services.http usage 
# how to extend base states
# how to add virtualhosts
# how to add or remove modules
include:
  - makina-states.services.http.apache
extend:
  makina-apache-main-conf:
    mc_apache:
      - version: 2.4
      - mpm: worker
  makina-apache-settings:
    file:
      - context:
        KeepAliveTimeout: 3
        worker_StartServers: "5"
        worker_MinSpareThreads: "60"
        worker_MaxSpareThreads: "120"
        worker_ThreadLimit: "120"
        worker_ThreadsPerChild: "60"
        worker_MaxRequestsPerChild: "1000"
        worker_MaxClients: "500"

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
            site = 'www.foobar.com',
            small_name = 'foobar',
            active = True,
            number = '900',
            log_level = 'debug',
            serverAlias = 'foobar.com',
            documentRoot = '/srv/projects/example/foobar/www',
            redirect_aliases = True,
            allow_htaccess = False) }}
