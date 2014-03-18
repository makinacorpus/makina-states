{# hooks for tomcat orchestration #}
tomcat-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-restart-hook
      - mc_proxy: tomcat-post-install-hook
      - mc_proxy: tomcat-pre-blocks-hook

tomcat-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: tomcat-pre-blocks-hook
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-post-restart-hook

tomcat-pre-blocks-hook:
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
