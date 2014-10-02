{# Icinga orchestration hooks #}
icinga-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-install
      - mc_proxy: icinga-pre-conf
      - mc_proxy: icinga-post-conf
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart
icinga-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-pre-conf
      - mc_proxy: icinga-post-conf
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart
icinga-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-conf
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart
icinga-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart

icinga-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-restart

icinga-post-restart:
  mc_proxy.hook: []


# hooks used for the add_configuration macro
icinga-configuration-pre-clean-directories:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-configuration-post-clean-directories

icinga-configuration-post-clean-directories:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-configuration-pre-accumulated-attributes-conf

icinga-configuration-pre-accumulated-attributes-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-configuration-post-accumulated-attributes-conf

icinga-configuration-post-accumulated-attributes-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-configuration-pre-object-conf

icinga-configuration-pre-object-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-configuration-post-object-conf


icinga-configuration-post-object-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-conf

