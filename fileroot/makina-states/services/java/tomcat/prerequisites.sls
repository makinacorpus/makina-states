include:
  - makina-states.services.java.tomcat.hooks
{% set data = salt['mc_tomcat.settings']() %}
{% set ver = data.ver %}
tomcat-{{ver}}-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - tomcat{{ ver }}
    - watch_in:
      - mc_proxy: tomcat-pre-restart-hook
    - require:
      - mc_proxy: makina-states-jdk_last
