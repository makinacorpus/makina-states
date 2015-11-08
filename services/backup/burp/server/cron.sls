{% set data = salt['mc_burp.settings']() %}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
burp-cron-cmd:
  file.managed:
    - source: salt://makina-states/files/usr/bin/burp-cron.sh
    - name: /usr/bin/burp-cron.sh
    - makedirs: true
    - mode: 755
    - template: jinja
    - user: root
    - use_vt: true

{% if data.cron_activated %}
burp-cron:
  file.managed:
    - source: "salt://makina-states/files/etc/cron.d/burpsynccron"
    - name: "/etc/cron.d/burpsynccron"
    - user: root
    - template: jinja
    - makedirs: true
    - use_vt: true
    - require:
      - file: burp-cron-cmd
{% else %}
burp-cron:
  file.absent:
    - name: "/etc/cron.d/burpsynccron"
{% endif %}
{% endif %}
