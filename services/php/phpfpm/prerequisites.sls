include:
  - makina-states.services.php.hooks
{% set phpSettings = salt['mc_php.settings']() %}

 {# Manage php-fpm packages @#}
makina-php-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - mc_proxy: makina-php-post-inst
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.php_fpm }}
{% if phpSettings.modules.xdebug.install %}
      - {{ phpSettings.packages.xdebug }}
{% endif %}
{% if phpSettings.modules.apc.install %}
      - {{ phpSettings.packages.apc }}
{% endif %}
