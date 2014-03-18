{# Hooks for php orchestration #}
#--- MAIN SERVICE RESTART/RELOAD watchers --------------
makina-php-pre-inst:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-php-pre-conf
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart

makina-php-post-inst:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-pre-conf
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart

makina-php-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart

makina-php-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart

# Note that mod_php does not have his own service
# (as opposed to php-fpm), and should in fact
# make an apache reload. So we'll fake a change
# here and tell apache to reload
makina-php-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-post-restart

makina-php-post-restart:
  mc_proxy.hook: []
