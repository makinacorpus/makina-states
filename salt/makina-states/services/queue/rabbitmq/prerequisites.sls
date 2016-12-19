{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set rabbitmqSettings = salt['mc_rabbitmq.settings']() %}
include:
  - makina-states.services.queue.rabbitmq.hooks

{% set dist = pkgssettings.udist %}
{% if grains['os'] in ['Debian'] %}
{% set mir = 'deb http://www.rabbitmq.com/debian/ testing main' %}
{% endif %}
rabbitmq-base:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: rabbitmq ppa
    - name: {{mir}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/rabbitmq.list
    - keyid: F7B8CEA6056E8E56
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: rabbitmq-pkgs

rabbitmq-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - librabbitmq-dev
      - rabbitmq-server
      - librabbitmq1
    - watch:
      - mc_proxy: rabbitmq-pre-install
    - watch_in:
      - mc_proxy: rabbitmq-pre-hardrestart
      - mc_proxy: rabbitmq-post-install


{% for i in rabbitmqSettings.rabbitmq.plugins %}
rabbitmq-plugins-{{i}}:
  cmd.run:
    - name: rabbitmq-plugins enable {{i}}
    - unless: test "x$(rabbitmq-plugins  list -e|awk '{print $2}'|egrep -q '^{{i}}$';echo ${?})" = "x0"
    - watch:
      - pkg: rabbitmq-pkgs
    - watch_in:
      - mc_proxy: rabbitmq-pre-hardrestart
      - mc_proxy: rabbitmq-post-install
{% endfor %}