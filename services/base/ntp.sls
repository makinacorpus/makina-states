{% import "makina-states/_macros/vars.jinja" as c with context %}
{% if c.ntp_en %}
ntp-pkgs:
  pkg.installed:
    - pkgs:
      - ntp
      - tzdata

ntpdate:
  pkg:
    - installed
{% if grains['os'] not in ['Debian', 'Ubuntu'] %}
  service:
    - enabled
{% endif %}

ntpd:
  service.running:
    - enable: True
{% if grains['os'] in ['Debian', 'Ubuntu'] %}
    - name: ntp
{% endif %}
    - watch:
      - file: /etc/ntp.conf
      - pkg: ntp-pkgs

/etc/ntp.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/ntp.conf
    - require:
      - pkg: ntp-pkgs

/etc/default/ntpdate:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/default/ntpdate
    - require:
      - pkg: ntp-pkgs
{% endif %}
