{# php + apache hooks integrations #}
include:
  - makina-states.services.http.apache-hooks
  - makina-states.services.php.php-hooks

makina-apache-php-pre-inst:
  mc_dummy.dummy:
    - require:
      - mc_dummy: makina-php-pre-inst
    - watch_in:
      - mc_dummy: makina-apache-pre-conf
      - mc_dummy: makina-apache-post-conf
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart
      - mc_dummy: makina-php-post-inst
      - mc_dummy: makina-php-pre-conf
      - mc_dummy: makina-php-post-conf
      - mc_dummy: makina-php-pre-restart
      - mc_dummy: makina-php-post-restart
      - mc_dummy: makina-apache-php-post-conf
      - mc_dummy: makina-apache-php-pre-conf
      - mc_dummy: makina-apache-php-post-conf
      - mc_dummy: makina-apache-php-pre-restart
      - mc_dummy: makina-apache-php-post-restart

{#
#  We need for php packages to install themselves to trigger
#  the correct MPM to be installed
#}
makina-apache-php-post-inst:
  mc_dummy.dummy:
    - require:
      - mc_dummy: makina-php-post-inst
    - watch_in:
      - mc_dummy: makina-apache-pre-inst
      - mc_dummy: makina-apache-post-inst

{# In most cases graceful reloads should be enough #}
makina-apache-php-pre-conf:
  mc_dummy.dummy:
    - require:
      - mc_dummy: makina-apache-pre-conf
    - watch_in:
      - mc_dummy: makina-php-pre-conf
      - mc_dummy: makina-apache-post-conf
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart
      - mc_dummy: makina-php-post-conf
      - mc_dummy: makina-php-pre-restart
      - mc_dummy: makina-php-post-restart
      - mc_dummy: makina-apache-php-post-conf
      - mc_dummy: makina-apache-php-pre-restart
      - mc_dummy: makina-apache-php-post-restart

makina-apache-php-post-conf:
  mc_dummy.dummy:
    - require:
      - mc_dummy: makina-apache-post-conf
    - watch_in:
      - mc_dummy: makina-apache-php-pre-restart
      - mc_dummy: makina-apache-php-post-restart
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart
      - mc_dummy: makina-php-post-conf
      - mc_dummy: makina-php-post-restart
      - mc_dummy: makina-php-pre-restart

{# In most cases graceful reloads should be enough #}
makina-apache-php-pre-restart:
  mc_dummy.dummy:
    - watch:
      - mc_dummy: makina-php-post-restart
    - watch_in:
      - mc_dummy: makina-apache-post-restart
      - mc_dummy: makina-apache-php-post-restart

makina-apache-php-post-restart:
  mc_dummy.dummy:
    - require:
      - mc_dummy: makina-apache-post-restart

