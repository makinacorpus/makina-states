{% set pkgssettings = salt['mc_pkgs.settings']()  %}

include:
  - makina-states.services.php.hooks
  - makina-states.localsettings.ssl.hooks
  - makina-states.services.db.mysql.hooks

makina-php-pre-fix-repos:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-fix-repos


makina-php-fix-repos:
  cmd.run:
    - name: sed -i -re "s/php5-5.6/php/g" /etc/apt/sources.list.d/phpppa.list && echo changed=False
    - stateful: true
    - dist: {{pkgssettings.udist}}
    - onlyif: test -e /etc/apt/sources.list.d/phpppa.list && grep php5-5.6 /etc/apt/sources.list.d/phpppa.list
    - watch:
      - mc_proxy: makina-php-pre-fix-repos
    - watch_in:
      - mc_proxy: makina-php-fix-repos
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ssl-certs-pre-install
      - mc_proxy: mysql-pre-install-hook
