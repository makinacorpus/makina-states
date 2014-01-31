{% set salts = salt['mc_salt.settings']() %}

include:
  -  makina-states.tests.base

testmode:
  buildout.installed:
    - name: {{salts.msr}}
    - config: test.cfg
    - require_in:
      - file: removeok
