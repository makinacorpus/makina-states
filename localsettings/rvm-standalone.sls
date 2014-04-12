{#-
# RVM integration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/rvm.rst
#}

{% macro do(full=True) %}
{% set rvms = salt['mc_rvm.settings']() %}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}
{{ salt['mc_macros.register']('localsettings', 'rvm') }}
{%- set locs = salt['mc_locations.settings']() %}
{%- macro rvm_env() %}
    - env:
      - rvm_prefix: {{locs.rvm_prefix}}
      - rvm_path: {{locs.rvm_path}}
{%- endmacro %}
{% if full %}
rvm-deps:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - names:
{# rvm deps #}
      - bash
      - coreutils
      - gzip
      - bzip2
      - gawk
      - sed
      - curl
      - git-core
      - subversion
{# mri-deps #}
      - build-essential
      - openssl
      - libreadline6
      - libreadline6-dev
      - curl
      - git-core
      - zlib1g
      - zlib1g-dev
      - libssl-dev
      - libyaml-dev
      - libsqlite3-0
      - libsqlite3-dev
      - sqlite3
      - libxml2-dev
      - libxslt1-dev
      - autoconf
      - libc6-dev
      - libncurses5-dev
      - automake
      - libtool
      - bison
      - subversion
      - ruby
      - ruby1.9.3

{{rvms.rvm_group}}-group:
  group.present:
    - name: {{rvms.rvm_group}}

{{rvms.rvm_user}}-user:
  user.present:
    - name: {{rvms.rvm_user}}
    - gid: {{rvms.rvm_group}}
    - home: /home/rvm
    - require:
      - group: {{rvms.rvm_group}}

rvm-dir:
 file.directory:
    - name: {{locs.rvm_path}}
    - group: {{rvms.rvm_group}}
    - user: {{rvms.rvm_user}}
    - require:
      - user: {{rvms.rvm_user}}
      - group: {{rvms.rvm_group}}

rvm-setup:
  cmd.run:
    - name: curl -s {{rvms.rvm_url}} | bash -s stable
    - unless: test -e {{locs.rvm_path}}/bin/rvm
    - require:
      - pkg: rvm-deps
      - file: rvm-dir
      - user:  {{rvms.rvm_user}}-user
{% endif %}

{%- for ruby in rvms.rubies %}
rvm-{{ruby}}:
  cmd.run:
    - name: {{locs.rvm}} install {{ruby}}
    - unless: test -e {{locs.rvm_path}}/rubies/{{ruby}}*/bin
    {% if full %}
    - require:
      - cmd: rvm-setup
    {% endif %}
{%- endfor %}

{% if full %}
active-rvm-bundler-hook:
  cmd.run:
    - name: {{saltmac.msr}}/_scripts/reset-perms.py' --dmode 0700 --fmode 0700 --paths "{{locs.rvm_path}}/hooks/after_cd_bundler"
{% endif %}
{% endmacro %}
{{ do(full=False)}}
