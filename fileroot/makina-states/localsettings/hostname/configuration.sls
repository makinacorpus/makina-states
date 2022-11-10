{#-
# Configure /etc/hostname entries based on pillar informations
# see:
#   - makina-states/doc/ref/formulaes/localsettings/hostname.rst
#}
include:
  - makina-states.localsettings.hostname.hooks

{% set mcn = salt['mc_network.settings']() %}
{# atomic file is not supported for /etc/hosts on a readonly layer (docker)
 # where the file can be written but not moved #}
{% if not salt['mc_nodetypes.is_docker']() %}
/etc/hostname-set1:
  cmd.run:
    - name: |
            set -ex
            chown root:root /etc/hostname
            chmod 644 /etc/hostname
            echo {{mcn.hostname}} > /etc/hostname
    - onlyif: |
              test "x$(cat /etc/hostname)" != "x{{mcn.hostname}}"
    - watch:
      - mc_proxy: makina-hostname-hostname-pre
    - watch_in:
      - mc_proxy: makina-hostname-hostname-post
/etc/hostname-set2:
  cmd.run:
    - name: "hostname {{mcn.hostname}}"
    - user: root
    - onlyif: |
              test "x$(hostname)" != "x{{mcn.hostname}}"
    - watch:
      - mc_proxy: makina-hostname-hostname-pre
    - watch_in:
      - mc_proxy: makina-hostname-hostname-post
{% endif %}
