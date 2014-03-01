salt-cloud-preinstall:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: salt-cloud-postinstall
salt-cloud-postinstall:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: salt-cloud-predeploy
salt-cloud-predeploy:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: salt-cloud-postdeploy
salt-cloud-postdeploy:
  mc_proxy.hook: []
