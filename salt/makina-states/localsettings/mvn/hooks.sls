include:
  - makina-states.localsettings.jdk.hooks

mvn-pre-prefix-install:
  mc_proxy.hook:
    - watch:
      - mc_proxy: makina-states-jdk_last
    - watch_in:
      - mc_proxy: mvn-post-prefix-install

mvn-post-prefix-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mvn-post-install

mvn-post-install:
  mc_proxy.hook: []
