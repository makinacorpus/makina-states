# The setup of makina-states is responsible for
# installing and keeping up & running the base salt infrastructure
#
# It will look in pillar & grains what bootstrap to apply
# Indeed, at bootstrap stage we have set a grain to tell which bootstrap we have
# run and we now have enought context to know how and what to upgrade
#
#, It will at least extend the boostrap process to:
#
# - Update makina-states before:
#   - Re buildout bootstrap
#   - Run buildout
#   - Run left relevant states in makina-states.services.bootstrap_*

{% set ms=salt['config.get']('bootstrap:mastersalt', False) -%}
{% set mmaster=salt['config.get']('mastersalt-master', False) -%}
{% set mminion=salt['config.get']('mastersalt-minion', False) -%}
{% set mastersalt=mmaster or mminion or ms -%}
{% set vm=salt['config.get']('bootstrap:makina-states-server', False) -%}
{% set server=salt['config.get']('bootstrap:makina-states-vm', False) -%}
{% set sa=salt['config.get']('bootstrap:makina-states-standalone', False) -%}
{% set msr='/srv/salt/makina-states' %}

include:
  {% if mastersalt %}
  - makina-states.services.bootstrap_mastersalt
  {% endif %}
  {% if server %}
  - makina-states.services.bootstrap_server
  {% elif sa %}
  - makina-states.services.bootstrap_standalone
  {% endif %}
  {% if vm %}
  - makina-states.services.bootstrap_vm
  {% else %}
  - makina-states.services.bootstrap
  {% endif %}
  {% if mmaster %}
  - makina-states.services.mastersalt_master
  {% endif %}

salt-buildout-bootstrap:
  cmd.run:
    - name: python bootstrap.py
    - cwd: {{msr}}
    - require:
      - git: makina-states
      - git: salt-git
      - git: m2crypto
      - git: SaltTesting

salt-buildout-run:
  cmd.run:
    - name: bin/buildout -N
    - cwd: {{msr}}
    - require_in:
      - service: salt-master
      - service: salt-minion
      {% if mmaster %}- service: mastersalt-master  {% endif %}
      {% if mmaster %}- service: mastersalt-minion  {% endif %}
    - require:
      - cmd: salt-buildout-bootstrap

