include:
  - makina-states.localsettings.pkgs.mgr
{# pin systemd proposed version  & install it#}
{% if grains['osrelease'] >= '15.04' and grains['os'] in ['Ubuntu'] %}
server-systemd-min:
  file.managed:
    - name: /etc/apt/preferences.d/99_systemd.pref
    - source: salt://makina-states/files/etc/apt/preferences.d/99_systemd.pref
    - user: root
    - makedirs: true
    - defaults:
        priority: 9999
    - template: jinja
    - group: root
    - mode: 644
    - require:
      - mc_proxy: ms-before-systemd
  {# pkg.latest do not handle well pinning upgrades #}
  cmd.watch:
    - name: |
            set -e
            apt-get update
            apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" install systemd
    - env:
        DEBIAN_FRONTEND: noninteractive
    - watch:
      - file: server-systemd-min
  pkg.latest:
    - pkgs: [systemd,
             libpam-systemd,
             libsystemd0,
             systemd-sysv]
    - require:
      - cmd: server-systemd-min
    - require_in:
      - mc_proxy: ms-after-systemd
{% endif %}
