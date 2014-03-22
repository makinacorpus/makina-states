{# hooks for tomcat orchestration #}
tomcat-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-conf-hook
      - mc_proxy: tomcat-post-conf-hook
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-blocks-hook
      - mc_proxy: tomcat-post-restart-hook
      - mc_proxy: tomcat-post-install-hook
      - mc_proxy: tomcat-pre-blocks-hook

tomcat-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-conf-hook
      - mc_proxy: tomcat-post-blocks-hook
      - mc_proxy: tomcat-post-conf-hook
      - mc_proxy: tomcat-pre-blocks-hook
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-restart-hook

tomcat-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-post-conf-hook
      - mc_proxy: tomcat-pre-blocks-hook
      - mc_proxy: tomcat-post-restart-hook
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-blocks-hook

tomcat-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-blocks-hook
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-restart-hook
      - mc_proxy: tomcat-post-blocks-hook

tomcat-pre-blocks-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-restart-hook
      - mc_proxy: tomcat-post-blocks-hook

tomcat-post-blocks-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-restart-hook

tomcat-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-post-restart-hook

tomcat-post-restart-hook:
  mc_proxy.hook: []
