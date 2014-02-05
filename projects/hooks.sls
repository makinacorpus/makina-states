prerequisites-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: precheckout-hook
      - mc_proxy: precheckout-salt-hook
      - mc_proxy: postcheckout-salt-hook
      - mc_proxy: precheckout-project-hook
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: preinstall-project-hook
      - mc_proxy: postinstall-project-hook

precheckout-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: precheckout-salt-hook
      - mc_proxy: postcheckout-salt-hook
      - mc_proxy: precheckout-project-hook
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: preinstall-project-hook
      - mc_proxy: postinstall-project-hook

precheckout-salt-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postcheckout-salt-hook
      - mc_proxy: precheckout-project-hook
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: preinstall-project-hook
      - mc_proxy: postinstall-project-hook

postcheckout-salt-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: precheckout-project-hook
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: preinstall-project-hook
      - mc_proxy: postinstall-project-hook

precheckout-project-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: preinstall-project-hook
      - mc_proxy: postinstall-project-hook

postcheckout-project-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: preinstall-project-hook
      - mc_proxy: postinstall-project-hook

preinstall-project-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postinstall-project-hook

postinstall-project-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: prerequisites-hook
      - mc_proxy: precheckout-hook
      - mc_proxy: precheckout-salt-hook
      - mc_proxy: postcheckout-salt-hook
      - mc_proxy: precheckout-project-hook
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: preinstall-project-hook

