{% set salts = salt['mc_salt.settings']() %}
{% set log = salts.msr+'/pep8.log' %}
include:
  -  makina-states.tests.base

pep8-makinastates-tests:
  cmd.run:
    - require_in:
      - file: markok
    - require:
      - file: removeok
    - name: |
            "{{salts.msr}}/bin/pep8" --ignore=E501 ,E12 "{{salts.msr}}/mc_states" 2>&1 > "{{log}}";
            ret=$?;
            cat "{{log}}";
            exit $ret
    - cwd: {{salts.msr}}

