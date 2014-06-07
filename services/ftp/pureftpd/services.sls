include:
  - makina-states.services.ftp.pureftpd.hooks

pure-ftpd-service:
  service.running:
    - name: pure-ftpd
    - watch:
      - mc_proxy: ftpd-pre-restart-hook
    - watch_in:
      - mc_proxy: ftpd-post-restart-hook
