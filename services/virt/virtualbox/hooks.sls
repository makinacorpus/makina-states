{# virtualbox orchestration hooks #}
include:
  - makina-states.localsettings.desktoptools.hooks
virtualbox-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-post-install
      - mc_proxy: virtualbox-pre-conf
      - mc_proxy: virtualbox-post-conf
      - mc_proxy: virtualbox-pre-restart
      - mc_proxy: virtualbox-post-restart

virtualbox-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-pre-conf
      - mc_proxy: virtualbox-post-conf
      - mc_proxy: virtualbox-pre-restart
      - mc_proxy: virtualbox-post-restart

virtualbox-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-post-conf
      - mc_proxy: virtualbox-pre-restart
      - mc_proxy: virtualbox-post-restart

virtualbox-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-pre-restart
      - mc_proxy: virtualbox-post-restart

virtualbox-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-post-restart

virtualbox-post-restart:
  mc_proxy.hook: []

virtualbox-pre-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-post-hardrestart

virtualbox-post-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: virtualbox-post-inst

virtualbox-post-inst:
  mc_proxy.hook: []
