{% set phpSettings = salt['mc_php.settings']()  %}
include:
  - makina-states.services.php.hooks
{# Manage php-fpm packages #}
makina-mod_php-exclude-fpm-pkg:
  pkg.removed:
    - pkgs:
      - {{ phpSettings.packages.php_fpm }}
      - {{ phpSettings.packages.mod_fcgid }}
      - {{ phpSettings.packages.php5_cgi }}
    - watch_in:
      - mc_proxy: makina-php-pre-inst

makina-modphp-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.mod_php }}
      {% if phpSettings.xdebug_install -%}
      - {{ phpSettings.packages.xdebug }}
      {%- endif %}
      {% if phpSettings.apc_install -%}
      - {{ phpSettings.packages.apc }}
      {%- endif %}
    - require:
      - mc_proxy: makina-php-pre-inst
    {# mod_php packages alteration needs an apache restart #}
    - watch_in:
      - mc_proxy: makina-php-post-inst
