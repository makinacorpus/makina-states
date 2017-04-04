{%- set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_ms_iptables.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.firewall.ms_iptables.hooks
ms_iptables-pkgs:
  pkg.latest:
  #pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{data.packages}}
    - require_in:
      - mc_proxy: ms_iptables-postinstall

msiptables_repo:
  file.directory:
    - name: {{locs.apps_dir}}/ms_iptables
    - user: root
    - mode: 700
    - makedirs: true
  mc_git.latest:
    - require:
      - file: msiptables_repo
    - name: https://github.com/corpusops/ms_iptables.git
    - target: {{locs.apps_dir}}/ms_iptables
    - user: root
    - require_in:
      - mc_proxy: ms_iptables-postinstall

