include:
  - makina-states.services.php.hooks
{% set phpSettings = salt['mc_php.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
makina-php-pkgs:
  pkg.latest:
    - watch:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - mc_proxy: makina-php-post-inst
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.php_fpm }}
{% if phpSettings.xdebug_install %}
      - {{ phpSettings.packages.xdebug }}
{% endif %}
{% if phpSettings.apc_install %}
      - {{ phpSettings.packages.apc }}
{% endif %}
