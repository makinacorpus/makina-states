# This file is an example of makina-states.services.php.phpfpm usage
# @see php_example if you work with mod_php and not php-fpm
# TODO: document
#
# WARNING, because of FastCgiIpcDir path, and socket path used in phpfpm pool
# relative to the project's root this states will only allow for ONE PHP-FPM+APACHE install,
# If you need several PHP-FPM website on one server, make another (extend) fastcgi.conf file
# manager and set shared_mode to True. Then fix the default on the php-fpm pools to use this path
# for sockets by setting the use_shared_socket_path parameter.
#
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{% set phpSettings = services.phpSettings %}

include:
  # IMPORTANT: If you use Apache, include it BEFORE phpfpm, so that
  # we can detect apache is used and trigger the restart in case of mod_php removal
  #- makina-states.services.http.nginx
  - makina-states.services.php.phpfpm_with_apache
  - makina-states.services.php.phpfpm
extend:
  makina-apache-main-conf:
    mc_apache:
      - mpm: "{{ salt['pillar.get']('project-foobar-apache-mpm', 'event') }}"
  makina-phpfpm-apache-module_connect_phpfpm_mod_fastcgi_module_conf:
    file.managed:
      - context:
          shared_mode: False
          project_root: '{{ locs.projects_dir }}/php.example.com'
          socket_directory: '/var/fcgi/'

# Adding some php packages 
my-phpfpm-other-modules:
  pkg.installed:
    - pkgs:
      - {{ phpSettings.packages.pear }}
    - require_in:
      - pkg: makina-php-pkgs
# Ensuring some other are not there
# Note that you cannot remove a module listed in makina-mod_php-pkgs
my-phpfpm-removed-modules:
  pkg.removed:
    - pkgs:
      - {{ phpSettings.packages.memcached }}
    - require_in:
      - pkg: makina-php-pkgs


{% from 'makina-states/services/php/php_macros.jinja' import pool with context %}
{{ pool(
        site= 'php.example.com',
        pool_name= 'devexample',
        settings= {
            'session_auto_start': True,
            'allow_url_fopen': True,
            'display_errors': True,
            'memory_limit': '256M',
            'upload_max_filesize': '100M',
            'max_input_vars': 3000,
            'fpm': {
                'socket_name':'myapp.sock'
            },
            'modules': {
                'apc': {
                    'user_entries_hint': 100,
                    'num_files_hint': 200,
                    'ttl': 0,
                    'user_ttl': 300,
                    'gc_ttl': 0,
                    'shm_size': '32M'
                 }
             }
        },
        include_path_additions= ':/tmp/foo:/foo/bar'
) }}

# Custom Apache Virtualhost
{% from 'makina-states/services/http/apache_macros.jinja' import virtualhost with context %}
{{ virtualhost(
          site = salt['pillar.get']('project-foobar-apache-vh1-name', 'php.example.com'),
          small_name = salt['pillar.get']('project-foobar-apache-vh1-nickname', 'phpexample'),
          active = True,
          number = '990',
          log_level = salt['pillar.get']('project-foobar-apache-vh1-loglevel', 'info'),
          documentRoot = salt['pillar.get']('project-foobar-apache-vh1-docroot', locs.projects_dir+'/php.example.com/www'),
          vh_in_template_source='salt://makina-states/files/etc/apache2/includes/in_virtualhost_drupal_phpfpm_template.conf',
          allow_htaccess = False,
          extra_jinja_apache_variables = {
              'socketName' : 'myapp.sock',
              'appConnTimeout' : 30,
              'idleTimeout' : 60,
              'allowed_files' : 'update.php|index.php|install.php|xmlrpc.php|cron.php'
          }
) }}

# very minimal index.php file
my-phpfpm-example-minimal-index:
  cmd.run:
    - name: echo "<?php phpinfo(); ?>" >> {{ locs.projects_dir }}/php.example.com/www/index.php; echo chown www-data:{{ localsettings.group }} {{ locs.projects_dir }}/php.example.com/www/index.php
    - require:
       - pkg: makina-php-pkgs
    - require_in:
        - file: makina-php-pool-devexample
