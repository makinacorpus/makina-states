include:
  - makina-states.services.java.tomcat.hooks

{% set data = salt['mc_tomcat.settings']() %}
{% set ver = data.ver %}
tomcat-{{ ver }}:
  service.running:
    - name: tomcat{{ ver }}
    - enable: true
    - watch_in:
      - mc_proxy: tomcat-pre-restart-hook
    - watch_in:
      - mc_proxy: tomcat-post-restart-hook
