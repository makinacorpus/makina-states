include:
  - makina-states.services.php.hooks
{% set phpSettings = salt['mc_php.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}

{# Manage php-fpm packages @#}
{% if grains['os'] in ['Ubuntu'] %}
makina-php-repos:
  pkgrepo.managed:
    - humanname: nginx ppa
    - name: deb http://ppa.launchpad.net/ondrej/php5-{{phpSettings.ppa_ver}}/ubuntu {{pkgssettings.ppa_dist}} main
    - dist: {{pkgssettings.ppa_dist}}
    - file: /etc/apt/sources.list.d/phpppa.list
    - keyid: E5267A6C
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - mc_proxy: makina-php-pkgs
      - mc_proxy: makina-php-post-inst

{% endif %}
makina-php-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
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
