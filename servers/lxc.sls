include:
  - makina-states.servers.base
  - makina-states.localsettings.hosts
  - makina-states.localsettings.pkgs


# be sure to have all grains
makina-lxc-proxy-dep:
  cmd.run:
    - name: /bin/true
    - requires:
      - cmd: salt-reload-grains
    - requires:
      - cmd: makina-lxc-proxy-dep
# no require_in as in bootstrap time we may not have yet rendered the lxc bits

# lxc container
{% if salt['config.get']('makina.lxc', False) %}
lxc-container-pkgs:
  pkg.installed:
    - names:
      - apt-utils
    - require_in:
      - cmd: makina-lxc-proxy-dep

makina-mark-as-lxc:
  cmd.run:
    - name: echo lxc > /run/container_type
    - unless: grep -q lxc /run/container_type
    - requires:
      - cmd: makina-lxc-proxy-dep

etc-init-lxc-setup:
  file.managed:
    - name: /etc/init/lxc-setup.conf
    - source: salt://makina-states/files/etc/init/lxc-setup.conf
    - user: root
    - group: root
    - mode: 0755
    - requires:
      - cmd: makina-mark-as-lxc

etc-init-lxc-stop:
  file.managed:
    - name: /etc/init/lxc-stop.conf
    - source: salt://makina-states/files/etc/init/lxc-stop.conf
    - user: root
    - group: root
    - mode: 0755
    - requires:
      - cmd: makina-mark-as-lxc

lxc-cleanup:
  file.managed:
    - name: /sbin/lxc-cleanup.sh
    - source: salt://makina-states/files/sbin/lxc-cleanup.sh
    - user: root
    - group: root
    - mode: 0755

lxc-install-non-harmful-packages:
  cmd.script:
    - source: salt://makina-states/_scripts/build_lxccorepackages.sh
    - requires:
      - cmd: makina-lxc-proxy-dep
      - cmd: makina-mark-as-lxc
      - file: lxc-cleanup
    - require_in:
      - pkg: ubuntu-pkgs
      - pkg: sys-pkgs

do-lxc-cleanup:
  cmd.run:
    - name: /sbin/lxc-cleanup.sh
    - requires:
      - file: lxc-cleanup
      - cmd: makina-lxc-proxy-dep
      - cmd: lxc-install-non-harmful-packages
      - pkg: ubuntu-pkgs
      - pkg: sys-pkgs
      - pkg: net-pkgs
      - pkg: dev-pkgs

# upstart based distro
{% if salt['config.get']('makina.upstart', False) %}
{% endif %}
{% endif %}
