{# docker orchestration hooks #}
include:
  - makina-states.localsettings.apparmor.hooks
docker-pre-install:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-apparmor-post
    - watch_in:
      - mc_proxy: docker-post-install
      - mc_proxy: docker-pre-conf
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-restart
      - mc_proxy: docker-post-restart

docker-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: docker-pre-conf
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-restart
      - mc_proxy: docker-post-restart

docker-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-restart
      - mc_proxy: docker-post-restart

docker-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: docker-pre-restart
      - mc_proxy: docker-post-restart

docker-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: docker-post-restart

docker-post-restart:
  mc_proxy.hook: []

docker-pre-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: docker-post-hardrestart

docker-post-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: docker-post-inst

docker-post-inst:
  mc_proxy.hook: []
