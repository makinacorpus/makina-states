{% set ulogdSettings = salt['mc_ulogd.settings']() %}
include:
  - makina-states.services.log.ulogd.hooks
ulogd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      {% if (salt['mc_utils.loose_version'](grains.get('osrelease', '')) >= salt['mc_utils.loose_version']('17.10') and grains['os'].lower() in ['ubuntu']) %}
      - ulogd2
      {% else %}
      - ulogd
      {% endif %}
    - watch:
      - mc_proxy: ulogd-pre-install-hook
    - watch_in:
      - mc_proxy: ulogd-pre-hardrestart-hook
      - mc_proxy: ulogd-post-install-hook
