# Rewriting apache stuff in custom state and module
# this is the test sls
# test this state with :
#  salt-call state.sls makina-states.services.http.apache2
apache-pkgs:
  pkg.installed:
    - names:
      - apache2
      - cronolog

apache-main-conf:
  mc_apache.deployed:
    - version: 2.4
    # see also mc_apache.include_module
    # and mc_apache.exclude_module
    # to alter theses lists from
    # other states (examples below)
    - modules_excluded:
      - autoindex
      - cgid
    - modules_included:
      - negotiation
      - rewrite
      - expires
      - headers
      - deflate
    - log_level: debug
    - require:
      - pkg.installed: apache-pkgs
      - mc_apache.include_module: apache-other-module-deflate-included
      - mc_apache.exclude_module: apache-other-module-excluded

# Extra module additions and removal
# Theses (valid) examples show you how
# to alter the modules_excluded and
# modules_included lists
apache-other-module-deflate-included:
  mc_apache.include_module:
    - modules:
      - status
    # not working, why?
    - require_in:
      - mc_apache.deployed: apache-main-conf

apache-other-module-excluded:
  mc_apache.exclude_module:
    - modules:
      - deflate
      - negotiation
    # not working, why?
    - require_in:
      - mc_apache.deployed: apache-main-conf


# Exemple of error: using a second mc_apache.deployed will fail
# as only one main apache configuration can be defined
# per server
apache-main-conf2:
  mc_apache.deployed:
    - version: 2.2
    - log_level: warn
    - require:
      - pkg.installed: apache-pkgs


#--- MAIN SERVICE RESTART/RELOAD watchers

makina-apache-service:
  service.running:
    - name: apache2
    - enable: True
    - require:
      - pkg.installed: apache-pkgs
    - watch:
      # restart service in case of package install
      - pkg.installed: apache-pkgs
      # restart service in case of main configuration changes
      - mc_apache.deployed: apache-main-conf
