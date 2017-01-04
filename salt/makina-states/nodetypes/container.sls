{% import "makina-states/_macros/h.jinja" as h with context %}
{# only really do if docker or lxc, because destructive #}
{% if salt['mc_nodetypes.is_container']() %}
{% set isDocker = salt['mc_nodetypes.is_docker']() %}
include:
  {% if not isDocker %}
  - makina-states.nodetypes.vm
  {% endif %}
  - makina-states.localsettings.pkgs.hooks
  - makina-states.nodetypes.container-hooks
container-container-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: [apt-utils, libfuse2]
    - watch:
      - mc_proxy: makina-lxc-proxy-pkgs-pre
    - watch_in:
      - mc_proxy: makina-lxc-proxy-pkgs
      - cmd: container-install-non-harmful-packages
      - cmd: container-do-cleanup

{% set extra_confs = {
  '/usr/bin/lxc-setup.sh': {"mode": "755"},
  '/etc/init/lxc-setup.conf': {"mode": "644"},
  '/etc/init/lxc-stop.conf': {"mode": "644"},
  '/sbin/build_lxccorepackages.sh': {
    "mode": "755",
    "source": "salt://makina-states/files/sbin/build_lxccorepackages.sh"},
  '/sbin/makinastates-snapshot.sh': {"mode": "755"},
  '/sbin/lxc-cleanup.sh': {"mode": "755"},
  '/sbin/reset-passwords.sh': {"mode": "755"},
  '/etc/systemd/system/lxc-stop.service': {"mode": "644"},
  '/etc/systemd/system/lxc-setup.service': {"mode": "644"},
  '/usr/bin/ms-lxc-stop.sh': {"mode": "755"}} %}
{% macro rmacro() %}
    - watch:
      - mc_proxy: makina-lxc-proxy-cfg
    - watch_in:
      - mc_proxy: makina-lxc-proxy-dep
{% endmacro %}
{{ h.deliver_config_files(extra_confs, after_macro=rmacro, prefix='lxc-conf-')}}

container-install-non-harmful-packages:
  cmd.run:
    - name: MS="{{salt['mc_locations.msr']()}}" /sbin/build_lxccorepackages.sh
    - watch:
      - mc_proxy: makina-lxc-proxy-build
    - watch_in:
      - mc_proxy: makina-lxc-proxy-mark

container-do-cleanup:
  cmd.run:
    - name: /sbin/lxc-cleanup.sh
    - watch:
      - mc_proxy: makina-lxc-proxy-cleanup
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end

{% if salt['mc_nodetypes.is_systemd']() and salt['mc_nodetypes.is_container']() %}
# apply a patch to be sure that future evols of the script are still compatible with our work
# (this patch wont apply in other case)
container-do-systemd-sysv-patch:
  file.managed:
    - name: /tmp/systemd-initd.patch
    - source: salt://makina-states/files/lib/lsb/init-functions.d/40-systemd.patch
    - onlyif: |
              set -e
              test -e /lib/lsb/init-functions.d/40-systemd
              if grep -q makinacorpus_container_init /lib/lsb/init-functions.d/40-systemd;then exit 1;fi
    - watch:
      - mc_proxy: makina-lxc-proxy-cleanup
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end
  cmd.run:
    - cwd: /
    - name: |
            set -e
            patch --dry-run -Np2 < /tmp/systemd-initd.patch
            patch -Np2 < /tmp/systemd-initd.patch
    - onlyif: |
              set -e
              test -e /lib/lsb/init-functions.d/40-systemd
              test -e /tmp/systemd-initd.patch
              if grep -q makinacorpus_container_init /lib/lsb/init-functions.d/40-systemd;then exit 1;fi
    - watch:
      - file: container-do-systemd-sysv-patch
      - mc_proxy: makina-lxc-proxy-cleanup
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end
# only enable, no stuff around
container-do-setup-services:
  cmd.run:
    - name: "systemctl enable lxc-setup;systemctl enable lxc-stop"
    - require:
      - mc_proxy: makina-lxc-proxy-cleanup
      - pkg: container-container-pkgs
    - require_in:
      - mc_proxy: makina-lxc-proxy-end
{% endif %}
{% endif %}
# vim:set nofoldenable:
