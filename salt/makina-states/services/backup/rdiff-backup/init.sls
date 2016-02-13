{#- Integration of rdiff-backup, a file backup software #}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.rdiff-backup') }}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{%- set data=salt['mc_rdiffbackup.settings']() %}
{%- set settings = salt['mc_utils.json_dump'](salt['mc_rdiffbackup.settings']()) %}
remove-rdiff-backup-pkgs:
  pkg.removed:
    - pkgs:
      - rdiff-backup
rdiff-backup-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkg: remove-rdiff-backup-pkgs
    - pkgs:
      - rdiff-backup
      - rdiff-backup-fs
      - librsync-dev
      - librsync1
      - python-dev
      - libattr1
      - libattr1-dev
      - libacl1
      - libacl1-dev
{# own rdiff wasnt working that well 
rdiff-backup:
  file.directory:
    - name: {{locs.apps_dir}}/rdiff-backup
    - user: root
    - mode: 700
    - makedirs: true
  mc_git.latest:
    - require:
      - pkg: rdiff-backup-pkgs
      - file: rdiff-backup
    - name: https://github.com/makinacorpus/rdiff-backup.git
    - target: {{locs.apps_dir}}/rdiff-backup
    - user: root

rdiff-backup-venv:
  virtualenv.managed:
    - require:
      - mc_git: rdiff-backup
    - requirements: {{locs.apps_dir}}/rdiff-backup/requirements.txt
    - system_site_packages: False
    - python: /usr/bin/python
    - name: {{locs.apps_dir}}/rdiff-backup/venv

rdiff-backup-install:
  cmd.run:
    - name: pwd;{{locs.apps_dir}}/rdiff-backup/venv/bin/python dist/setup.py develop
    - cwd: {{locs.apps_dir}}/rdiff-backup
    - user: root
    - unless: test -e {{locs.apps_dir}}/rdiff-backup/venv/bin/rdiff-backup
    - require:
      - virtualenv: rdiff-backup-venv

{% for bin in ['rdiff-backup', 'rdiff-backup-statistics'] %}
rdiff-backup-{{bin}}-bin:
  file.symlink:
    - name: {{locs.bin_dir}}/{{bin}}
    - target: {{locs.apps_dir}}/rdiff-backup/venv/bin/{{bin}}
    - require:
      - cmd: rdiff-backup-install

rdiff-backup-{{bin}}-man:
  file.symlink:
    - name: {{locs.usr_dir}}/share/man/man1/{{bin}}.1
    - target: {{locs.apps_dir}}/rdiff-backup/{{bin}}.1
    - require:
      - cmd: rdiff-backup-install
{%endfor%}
#}
{%endif %}
