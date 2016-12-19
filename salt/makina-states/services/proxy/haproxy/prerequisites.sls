{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set haproxySettings = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.localsettings.insserv

{% set f = salt['mc_locations.settings']().conf_dir + '/apt/sources.list.d/haproxy.list' %}

haproxy-base-cleanup:
  cmd.run:
    - names:
      - sed -i "/makinacorpus/ d" "{{f}}" && echo changed='false'
      - sed -i "/haproxy-1.5/ d" "{{f}}" && echo changed='false'
      - sed -i "/haproxy-1.6/ d" "{{f}}" && echo changed='false'
{% if salt['mc_haproxy.version']() >= '1.6' %}
      - |
        if grep "listen stats :" /etc/haproxy/cfg.d/listeners.cfg >/dev/null 2>&1; then
          rm -f /etc/haproxy/cfg.d/listeners.cfg
        fi
        echo changed='false'
{% endif %}
    - onlyif: test -e "{{f}}"
    - stateful: true
    - require_in:
      - pkgrepo: haproxy-base
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: haproxy-post-install-hook

haproxy-base:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: haproxy ppa
    - name: deb http://ppa.launchpad.net/vbernat/haproxy-1.7/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: "{{f}}"
    - keyid: 1C61B9CD
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: haproxy-pkgs

haproxy-pkgs:
  pkg.latest:
    - pkgs:
      - haproxy
    - watch:
      - mc_proxy: localsettings-inssserv-post
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: haproxy-post-install-hook

group-haproxy:
  group.present:
    - name: {{haproxySettings.group}}
user-haproxy:
  user.present:
    - name: {{haproxySettings.user}}
    - system: true
    - optional_groups: {{haproxySettings.group}}
    - remove_groups: false
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-post-install-hook