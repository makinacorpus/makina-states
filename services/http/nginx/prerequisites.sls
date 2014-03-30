include:
  - makina-states.services.http.nginx
makina-nginx-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - {{ salt['mc_nginx.settings']().package }}
    - watch:
      - mc_proxy: nginx-pre-install-hook
    - watch_in:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook
