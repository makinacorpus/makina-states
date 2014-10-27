{% set phpSettings = salt['mc_php.settings']() %}
include:
  - makina-states.services.php.hooks

#--- MAIN SERVICE RESTART/RELOAD watchers --------------
fpm-makina-php-restart:
  service.running:
    - name: {{ phpSettings.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch:
      # restart service in case of package install
      - mc_proxy: makina-php-pre-restart
    - require_in:
      # restart service in case of package install
      - mc_proxy: makina-php-post-restart

# In most cases graceful reloads should be enough
{# has problem with reload for now
fpm-makina-php-reload:
  service.running:
    - name: {{ phpSettings.service }}
    - watch:
      # reload service in case of package install
      - mc_proxy: makina-php-pre-restart
    - require_in:
      # reload service in case of package install
      - mc_proxy: makina-php-post-restart
    - enable: True
    # does not work pretty well, use complete restart - reload: True
#}
