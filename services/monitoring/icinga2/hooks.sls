{# Icinga orchestration hooks #}
icinga2-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-post-install
      - mc_proxy: icinga2-pre-conf
      - mc_proxy: icinga2-post-conf
      - mc_proxy: icinga2-pre-restart
      - mc_proxy: icinga2-post-restart
icinga2-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-pre-conf
      - mc_proxy: icinga2-post-conf
      - mc_proxy: icinga2-pre-restart
      - mc_proxy: icinga2-post-restart
icinga2-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-post-conf
      - mc_proxy: icinga2-pre-restart
      - mc_proxy: icinga2-post-restart
icinga2-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-pre-restart
      - mc_proxy: icinga2-post-restart

icinga2-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-post-restart

icinga2-post-restart:
  mc_proxy.hook: []


# hooks used for the add_configuration macro
icinga2-configuration-pre-clean-directories:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-configuration-post-clean-directories

icinga2-configuration-post-clean-directories:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-configuration-pre-accumulated-attributes-conf

icinga2-configuration-pre-accumulated-attributes-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-configuration-post-accumulated-attributes-conf

icinga2-configuration-post-accumulated-attributes-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-configuration-pre-object-conf

icinga2-configuration-pre-object-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-configuration-post-object-conf


icinga2-configuration-post-object-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga2-post-conf


