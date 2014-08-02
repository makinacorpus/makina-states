{# php + apache hooks integrations
# even if you do not use apache, the hooks are no op
# and are unharful but neccesary for orchestration
#}
include:
  - makina-states.services.http.apache.hooks

makina-php-pre-repo:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-php-pre-conf
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart
      - mc_proxy: makina-php-pre-inst

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

{# ------------------------------------ #}
{# SPECIFIC TO APACHE ORCHESTRATION     #}
{# ------------------------------------ #}
makina-apache-php-pre-inst:
  mc_proxy.hook:
    - require:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-php-pre-conf
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-apache-php-pre-conf
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-apache-php-pre-restart
      - mc_proxy: makina-apache-php-post-restart

{#
#  We need for php packages to install themselves to trigger
#  the correct MPM to be installed
#}
makina-apache-php-post-inst:
  mc_proxy.hook:
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-inst
      - mc_proxy: makina-apache-post-inst

{# In most cases graceful reloads should be enough #}
makina-apache-php-pre-conf:
  mc_proxy.hook:
    - require:
      - mc_proxy: makina-apache-pre-conf
    - watch_in:
      - mc_proxy: makina-php-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_proxy: makina-php-post-restart
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-apache-php-pre-restart
      - mc_proxy: makina-apache-php-post-restart

makina-apache-php-post-conf:
  mc_proxy.hook:
    - require:
      - mc_proxy: makina-apache-post-conf
    - watch_in:
      - mc_proxy: makina-apache-php-pre-restart
      - mc_proxy: makina-apache-php-post-restart
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart
      - mc_proxy: makina-php-post-conf
      - mc_proxy: makina-php-post-restart
      - mc_proxy: makina-php-pre-restart

{# In most cases graceful reloads should be enough #}
makina-apache-php-pre-restart:
  mc_proxy.hook:
    - watch:
      - mc_proxy: makina-php-post-restart
    - watch_in:
      - mc_proxy: makina-apache-post-restart
      - mc_proxy: makina-apache-php-post-restart

makina-apache-php-post-restart:
  mc_proxy.hook:
    - require:
      - mc_proxy: makina-apache-post-restart
