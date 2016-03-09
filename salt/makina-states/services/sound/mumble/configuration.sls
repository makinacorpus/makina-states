{% set data = salt['mc_mumble.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.sound.mumble.hooks
  - makina-states.services.sound.mumble.services
{% for f in ['/etc/default/mumble-server',
             '/etc/mumble-server.ini']%}
makina-mumble-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: mumble-pre-conf-hook
    - watch_in:
      - mc_proxy: mumble-post-conf-hook
{% endfor %}
