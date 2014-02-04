{#
# This file is an example of makina-states.services.php.phpfpm usage
# @see php_example if you work with mod_php and not php-fpm
# TODO: document
#
# WARNING, because of FastCgiIpcDir path, and socket path used in phpfpm pool
# relative to the project's root this states will only allow for ONE PHP-FPM+APACHE install,
# If you need several PHP-FPM website on one server, make another (extend) fastcgi.conf file
# manager and set shared_mode to True. Then fix the default on the php-fpm pools to use this path
# for sockets by setting the use_shared_socket_path parameter.
#}
{% import "makina-states/_macros/php.jinja" as php with context %}

{# Ensuring some other are not there
#  Note that you cannot remove a module listed in makina-mod_php-pkgs #}
my-phpfpm-removed-modules:
  pkg.removed:
    - pkgs:
      - {{ phpSettings.packages.memcached }}
    - require_in:
      - mc_proxy: makina-apache-php-pre-inst

{# Adding some php packages #}
my-phpfpm-other-modules:
  pkg.installed:
    - pkgs:
      - {{ phpSettings.packages.pear }}
    - require_in:
      - mc_proxy: makina-apache-php-post-inst

{% set drupal = 'salt://makina-states/files/etc/apache2/includes/in_virtualhost_drupal_phpfpm_template.conf' %}
{{ php.apache_fpm_virtualhost(
   'example.com',
   'apache_vhost_opts': {
      'server_aliases': ['test.com'],
      'vh_in_template_source': drupal,
      'extra_jinja_apache_variables' : {
          'appConnTimeout' : 30,
          'idleTimeout' : 60,
          'allowed_files' : 'update.php|index.php|install.php|xmlrpc.php|cron.php'
      },
   }
   fpmpool_opts: {
      'include_path_additions': ':/tmp/foo:/foo/bar',
      'settings': {
            'session_auto_start': True,
            'allow_url_fopen': True,
            'display_errors': True,
            'memory_limit': '256M',
            'upload_max_filesize': '100M',
            'max_input_vars': 3000,
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
      }
   }) }}
