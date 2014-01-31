{% set salts = salt['mc_salt.settings']() %}
testmode:
  buildout.installed:
    - name: {{salts.msr}}
    - config: test.cfg
    - require_in:
      - file: removeok
