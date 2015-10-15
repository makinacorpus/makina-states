{#-
# RVM integration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/rvm.rst
#}

{% set rvms = salt['mc_rvm.settings']() %}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}
{{ salt['mc_macros.register']('localsettings', 'rvm') }}
{%- set locs = salt['mc_locations.settings']() %}
{%- macro rvm_env() %}
    - env:
      - rvm_prefix: {{locs.rvm_prefix}}
      - path: {{locs.rvm_path}}
{%- endmacro %}
rvm-deps:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
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

{{rvms.group}}-group:
  group.present:
    - name: {{rvms.group}}

{{rvms.user}}-user:
  user.present:
    - name: {{rvms.user}}
    - gid: {{rvms.group}}
    - home: /home/rvm
    - require:
      - group: {{rvms.group}}

rvm-dir:
 file.directory:
    - name: {{locs.rvm_path}}
    - group: {{rvms.group}}
    - user: {{rvms.user}}
    - require:
      - user: {{rvms.user}}
      - group: {{rvms.group}}

rvm-setup:
  cmd.run:
    - name: |
            cd /tmp
            wget -O rvm-installer "{{rvms.url}}"
            chmod +x rvm-installer
            curl -sSL https://rvm.io/mpapis.asc | gpg --import -
            ./rvm-installer {{rvms.branch}} && {{locs.rvm}} fix-permissions
    - use_vt: true
    - unless: test -e {{locs.rvm_path}}/bin/rvm
    - require:
      - pkg: rvm-deps
      - file: rvm-dir
      - user:  {{rvms.user}}-user


{% macro install_ruby(version, suf='') %}
rvm-{{version}}{{suf}}:
  cmd.run:
    - name: {{locs.rvm}} install {{version}} && {{locs.rvm}} fix-permissions
    - use_vt: true
    - unless: test -e {{locs.rvm_path}}/rubies/*{{version}}*/bin
    - require_in:
      - cmd: active-rvm-bundler-hook
    - require:
      - cmd: rvm-setup
{% endmacro %}

{%- for ruby in rvms.rubies %}
{{install_ruby(ruby)}}
{%- endfor %}

active-rvm-bundler-hook:
  cmd.run:
    - name: {{saltmac.msr}}/_scripts/reset-perms.py --no-acls --dmode 0700 --fmode 0700 --paths "{{locs.rvm_path}}/hooks/after_cd_bundler"
    - require_in:
      - mc_proxy: rvm-last

rvm-last:
  mc_proxy.hook: []


{% macro rvm(cmd, state='rvm', version='1.9.3', gemset='global', user='root', vt=True) %}
{{state}}:
  cmd.run:
    - name: >
            bash --login -c ". /etc/profile
            && . /usr/local/rvm/scripts/rvm
            && rvm --create use {{version.strip()}}@{{gemset.strip()}}
            && {{cmd}}"
    {% if vt %}
    - use_vt: {{vt}}
    {%endif%}
{% endmacro %}
