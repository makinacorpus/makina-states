{# Hooks for jdk integration #}
makina-states-jdk_begin:
  mc_proxy.hook: []

makina-states-jdk_last:
  mc_proxy.hook:
    - watch:
      - mc_proxy: makina-states-jdk_begin
