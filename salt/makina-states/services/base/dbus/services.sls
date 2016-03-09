include:
  - makina-states.services.base.dbus.hooks
{% if not salt['mc_nodetypes.is_container']() %}
makina-dbus-service:
  service.running:
    - name: dbus
    - enable: true
    - watch:
      - mc_proxy: dbus-prerestart
    - watch_in:
      - mc_proxy: dbus-postrestart

makina-dbus-restart-service:
  service.running:
    - name: dbus
    - enable: true
    - watch:
      - mc_proxy: dbus-prehardrestart
    - watch_in:
      - mc_proxy: dbus-posthardrestart
{% endif %}
