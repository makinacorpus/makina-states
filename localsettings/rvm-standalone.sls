{% macro do(full=True) %}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}
{{ salt['mc_macros.register']('localsettings', 'rvm') }}
{%- set locs = localsettings.locations %}
{%- macro rvm_env() %}
    - env:
      - rvm_prefix: {{locs.rvm_prefix}}
      - rvm_path: {{locs.rvm_path}}
{%- endmacro %}
{% if full %}
rvm-deps:
  pkg.installed:
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

{{localsettings.rvm_group}}-group:
  group.present:
    - name: {{localsettings.rvm_group}}

{{localsettings.rvm_user}}-user:
  user.present:
    - name: {{localsettings.rvm_user}}
    - gid: {{localsettings.rvm_group}}
    - home: /home/rvm
    - require:
      - group: {{localsettings.rvm_group}}

rvm-dir:
 file.directory:
    - name: {{locs.rvm_path}}
    - group: {{localsettings.rvm_group}}
    - user: {{localsettings.rvm_user}}
    - require:
      - user: {{localsettings.rvm_user}}
      - group: {{localsettings.rvm_group}}

rvm-setup:
  cmd.run:
    - name: curl -s {{localsettings.rvm_url}} | bash -s stable
    - unless: test -e {{locs.rvm_path}}/bin/rvm
    - require:
      - pkg: rvm-deps
      - file: rvm-dir
      - user:  {{localsettings.rvm_user}}-user
{% endif %}

{%- for ruby in localsettings.rubies %}
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
  cmd.script:
    - source: 'file://{{saltmac.msr}}/_scripts/reset-perms.sh'
    - template: jinja
    - msr: {{ saltmac.msr }}
    - dmode: 0700
    - fmode: 0700
    - reset_paths:
      - {{locs.rvm_path}}/hooks/after_cd_bundler
{% endif %}
{% endmacro %}
{{ do(full=False)}}
