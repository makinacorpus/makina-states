{% set salts = salt['mc_salt.settings']() %}
removeok:
  file.absent:
    - name: /tmp/testok

markok:
  file.touch:
    - name: /tmp/testok

