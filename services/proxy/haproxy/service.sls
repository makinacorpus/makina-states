include:
  - makina-states.services.proxy.haproxy.hooks

makina-haproxy-service:
  service.running:
    - name: haproxy
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: haproxy-pre-restart-hook
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook

makina-haproxy-restart-service:
  service.running:
    - name: haproxy
    - enable: true
    - watch:
      - mc_proxy: haproxy-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook
