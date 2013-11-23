include:
  - makina-states.servers.base
  - makina-states.localsettings.hosts

# be sure to have all grains
makina-lxc-proxy-dep:
  cmd:
    - name: /bin/true
    - requires:
      - cmd: salt-reload-grains

# lxc container
{% if config.get('makina.lxc', False) '%}

# upstart based distro
{% if config.get('makina.upstart', False) '%}
{% endif %}
{% endif %}
