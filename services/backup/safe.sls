# This states file aims to configure and manage postgresql clusters
# throught their respective unix sockets.
#
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set services = services %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{{ services.register('backup.safe') }}

include:
  - {{ services.localsettings.statesPref }}rvm

{% set rvm = locs.rvm %}
{% set rb = localsettings.rubies[0] %}
{% set reqs = 'rubygems-bundler' %}
{% set app = 'astrailsafe'  %}
{% set rapp = rb+"@"+app %}
{% set prefix = locs.apps_dir+'/safe' %}
{% set gpath = "\""+locs.rvm_path+'/gems/'+rb+"\"*\"@"+app+"\"" %}
{% set rdo = "\""+rvm+"\" "+rapp+" do" %}

{{app}}-app:
  cmd.run:
    - name: '"{{rvm}}" {{rb}} do "{{rvm}}" gemset create {{app}}'
    - unless: test -e {{gpath}}
    - require:
      - cmd: rvm-{{rb}}

{{app}}-git:
  file.directory:
    - name: {{prefix}}
    - makedirs: true
  git.latest:
    - name: https://github.com/makinacorpus/safe.git
    - target: {{prefix}}
    - require:
      - file: {{app}}-git

{{app}}-install-gem:
  cmd.run:
    - name: '{{rdo}} gem install {{reqs}}'
    - unless: test -e {{gpath}}/gems/rubygems-bundler-*
    - cwd: {{prefix}}
    - require:
      - cmd: {{app}}-app
      - git: {{app}}-git

{{app}}-install-app:
  cmd.run:
    - name: '{{rdo}} bundle install --binstubs=./bundler_stubs'
    - unless: test -e {{gpath}}/gems/net-ssh-*
    - cwd: {{prefix}}
    - require:
      - git: {{app}}-git
      - cmd: {{app}}-install-gem


{{app}}-wrappers-app:
  cmd.run:
    - name: '{{rdo}} "{{rvm}}" alias create "{{app}}" "{{rapp}}"'
    - unless: test -e "{{locs.rvm_path}}/wrappers/{{app}}"
    - cwd: {{prefix}}
    - require:
      - cmd: {{app}}-install-app

