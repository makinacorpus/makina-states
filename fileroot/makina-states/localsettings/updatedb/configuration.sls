include:
  - makina-states.localsettings.updatedb.hooks

{% set data = salt['mc_updatedb.settings']() %}
{% for f in ['/etc/updatedb.conf'] %}
etc-update-{{f}}:
  file.managed:
    - watch:
      - mc_proxy: updatedb-post-install
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - mode: 700
    - user: root
    - template: jinja
    - makedirs: true
    - group: root
{% endfor %}
