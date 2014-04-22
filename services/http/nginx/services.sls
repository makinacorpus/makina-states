include:
  - makina-states.services.http.nginx.hooks
#--- MAIN SERVICE RESTART/RELOAD watchers --------------
# Configuration checker, always run before restart of graceful restart
makina-nginx-conf-syntax-check:
  cmd.run:
    - name: {{ salt['mc_salt.settings']().msr }}/_scripts/nginxConfCheck.sh
    - stateful: True
    - watch:
       - mc_proxy: nginx-pre-restart-hook
    - watch_in:
       - mc_proxy: makina-nginx-restart

makina-nginx-restart:
  service.running:
    - name: {{ salt['mc_nginx.settings']().service }}
    - enable: True
    - watch_in:
      - mc_proxy: nginx-post-restart-hook
    - watch:
      - mc_proxy: nginx-pre-restart-hook


makina-nginx-reload:
  service.running:
    - name: {{ salt['mc_nginx.settings']().service }}
    - enable: True
    - reload: True
    - watch:
      - mc_proxy: nginx-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: nginx-post-hardrestart-hook
