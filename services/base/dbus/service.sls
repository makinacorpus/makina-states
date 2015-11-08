include:
  - makina-states.services.base.dbus.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() and not salt['mc_nodetypes.is_container']() %}
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
