include:
  - makina-states.services.virt.docker.hooks
  - makina-states.services.virt.lxc.hooks
{% if grains['os'] in ['Debian'] -%}
docker-mount-cgroup:
  mount.mounted:
    - name: /sys/fs/cgroup
    - device: none
    - fstype: cgroup
    - mkmnt: True
    - opts:
      - defaults
    - watch:
      - mc_proxy: docker-pre-conf
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: lxc-post-conf
{% endif %}
