{# specific install rules on devhost for lxc managment #}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.cloud.generic.hooks.compute_node

cloud-lxc-devhost-symdir:
  file.directory:
    - name: /srv/lxc
    - makedirs: true

cloud-lxc-devhost-refresh-symlinks:
  cmd.run:
    - name: |
            cd /srv/lxc && rm * && for i in $(find /var/lib/lxc/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null);do
              ln -sf ../..${i}/rootfs $(basename ${i})
            done
    - watch:
      - file: cloud-lxc-devhost-symdir
      - mc_proxy: salt-cloud-lxc-devhost-hooks

