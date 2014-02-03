{# Hooks for apache orchestration #}
makina-apache-pre-inst:
  mc_dummy.dummy:
    - watch_in:
      - mc_dummy: makina-apache-post-inst
      - mc_dummy: makina-apache-pre-conf
      - mc_dummy: makina-apache-post-conf
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart
      - mc_dummy: makina-apache-post-pkgs

makina-apache-post-pkgs:
  mc_dummy.dummy:
    - watch_in:
      - mc_dummy: makina-apache-post-inst
      - mc_dummy: makina-apache-pre-conf
      - mc_dummy: makina-apache-post-conf
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart

makina-apache-post-inst:
  mc_dummy.dummy:
    - watch_in:
      - mc_dummy: makina-apache-pre-conf
      - mc_dummy: makina-apache-post-conf
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart

makina-apache-pre-conf:
  mc_dummy.dummy:
    - watch_in:
      - mc_dummy: makina-apache-post-conf
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart

makina-apache-post-conf:
  mc_dummy.dummy:
    - watch_in:
      - mc_dummy: makina-apache-pre-restart
      - mc_dummy: makina-apache-post-restart

makina-apache-pre-restart:
  mc_dummy.dummy:
    - watch_in:
      - mc_dummy: makina-apache-post-restart

makina-apache-post-restart:
  mc_dummy.dummy: []
