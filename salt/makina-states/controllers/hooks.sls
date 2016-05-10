{#- Dummies states for orchestration and reuse in standalone modes #}
{#- only here for orchestration purposes #}
dummy-pre-salt-pkg-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dummy-pre-salt-pkg-post
dummy-pre-salt-pkg-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dummy-pre-salt-checkouts
dummy-pre-salt-checkouts:
  mc_proxy.hook: []
dummy-pre-salt-service-restart:
  mc_proxy.hook: []
dummy-post-salt-service-restart:
  mc_proxy.hook: []
dummy-salt-layout:
  mc_proxy.hook: []
{# retrocompat: do not remove the service hooks #}
dummy-pre-minion-service-restart:
  mc_proxy.hook:
    - require:
      - mc_proxy: dummy-pre-salt-service-restart
      - mc_proxy: dummy-pre-mastersalt-service-restart
dummy-post-minion-service-restart:
   mc_proxy.hook:
    - require:
      - mc_proxy: dummy-post-salt-service-restart
      - mc_proxy: dummy-post-mastersalt-service-restart
dummy-pre-master-service-restart:
  mc_proxy.hook:
    - require:
      - mc_proxy: dummy-pre-salt-service-restart
      - mc_proxy: dummy-pre-mastersalt-service-restart
dummy-post-master-service-restart:
   mc_proxy.hook:
    - require:
      - mc_proxy: dummy-post-salt-service-restart
      - mc_proxy: dummy-post-mastersalt-service-restart
dummy-pre-salt-minion-service-restart:
  mc_proxy.hook: []
dummy-pre-salt-master-service-restart:
  mc_proxy.hook: []
dummy-post-salt-minion-service-restart:
   mc_proxy.hook:
    - require_in:
      - mc_proxy: dummy-post-salt-service-restart
dummy-post-salt-master-service-restart:
   mc_proxy.hook:
    - require_in:
      - mc_proxy: dummy-post-salt-service-restart
dummy-pre-mastersalt-minion-service-restart:
  mc_proxy.hook: []
dummy-pre-mastersalt-master-service-restart:
  mc_proxy.hook: []
dummy-post-mastersalt-minion-service-restart:
   mc_proxy.hook:
    - require_in:
      - mc_proxy: dummy-post-mastersalt-service-restart
dummy-post-mastersalt-master-service-restart:
   mc_proxy.hook:
    - require_in:
      - mc_proxy: dummy-post-mastersalt-service-restart
dummy-pre-mastersalt-service-restart:
  mc_proxy.hook: []
dummy-post-mastersalt-service-restart:
  mc_proxy.hook: []
dummy-pre-mastersalt-checkouts:
  mc_proxy.hook: []
dummy-mastersalt-layout:
  mc_proxy.hook: []
