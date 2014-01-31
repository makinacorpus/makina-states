{% set salts = salt['mc_salt.settings']() %}
{% set log = salts.msr+'/pylint.log' %}
{% set rc = salts.msr + "/src/salt/.testing.pylintrc" %}
include:
  -  makina-states.tests.base

lint-makinastates-tests:
  cmd.run:
    - require_in:
      - file: markok
    - require:
      - file: removeok
    - name: |
            "{{salts.msr}}/bin/pylint" --rcfile="{{rc}}" "{{salts.msr}}/mc_states" 2>&1 > "{{log}}";
            ret=$?;
            cat "{{log}}";
            exit $ret
    - cwd: {{salts.msr}}

