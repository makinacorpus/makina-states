include:
  - makina-states.controllers.hooks
{%- set locs = salt['mc_locations.settings']() %}
{%- set settings = salt['mc_salt.settings']() %}
{% if settings.use_mc_pillar %}
lnk-extpillar-inventory:
  file.symlink:
    - name: {{ settings.msr }}/etc/ansible/inventories/makinastates.py
    - target: {{ settings.msr }}/ansible/inventories/makinastates.py
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
{% else %}
unlnk-extpillar-inventory:
  file.absent:
    - name: {{ settings.msr }}/etc/ansible/inventories/makinastates.py
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
{% endif %}

salt-restrict-conf:
  file.directory:
    - names: ["{{settings.msr}}/pillar", "{{settings.msr}}/etc"]
    - mode: 700
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart 
