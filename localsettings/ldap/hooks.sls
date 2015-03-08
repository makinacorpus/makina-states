localldap-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: localldap-post-install
      - mc_proxy: localldap-pre-conf
      - mc_proxy: localldap-post-conf

localldap-post-install:
  mc_proxy.hook: 
    - watch_in:
      - mc_proxy: localldap-pre-conf
      - mc_proxy: localldap-post-conf

localldap-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: localldap-post-conf 

localldap-post-conf:
  mc_proxy.hook: []  
