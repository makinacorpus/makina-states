include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.localsettings.ssl.hooks

makina-haproxy-service:
  service.running:
    - name: haproxy
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook

makina-haproxy-restart-service:
  service.running:
    - name: haproxy
    - enable: true
    - watch:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook
