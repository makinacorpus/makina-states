{% set d = "{0}/makina-states/tests/dumbhttp".format(salt['pillar.get']('master')['file_roots']['base'][0]) %}
{% set w = salt['mc_utils.get']('bottleapp_dir', '/srv/bottleapp') %}
installbottle:
  virtualenv.managed:
    - name: {{w}}
    - pip_pkgs: [bottle, bottledaemon]
  file.managed:
    - name: {{w}}/app.sh
    - mode: 750
    - contents : |
          {# XXX: lockfile doesnt play well with vbox guestfs ... #}
          rsync -azv --delete {{d}}/ {{w}}/a/ || exit 1
          cd {{w}}/a
          # stop does not work well also...
          ps afux|grep app.py|awk '{print $2}'|xargs kill -9
          rm -rf *pid *lock
          . ../bin/activate
          python app.py start
    - require:
      - virtualenv: installbottle
  cmd.run:
    - name: {{w}}/app.sh
    - require:
      - file: installbottle
      - virtualenv: installbottle
