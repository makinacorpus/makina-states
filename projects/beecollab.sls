{%- import "makina-states/projects/zope.jinja" as zope with context %}
{%- set services = zope.services %}
{%- set localsettings = zope.localsettings %}

{% macro install_dependancies(common) %}
{% if common.full %}
beecollab_install_dependancies:
  pkg.installed:
    - pkgs:
      - ffmepg
      - ffmpeg2theora
{% endif %}
{% endmacro %}

{% macro install_zope(common) %}
{{ zope.install_generic_zope_project(*varargs, **kwargs) }}
{% endmacro %}

{% macro install_etherpad(common) %}
{% endmacro %}

{% macro install_setup(common) %}
{# Install npm + npm install in resources/dev + grunt #}
{% if common.full %}
beecollab_project_setup_grunt-cli:
  npm.installed:
    - name: grunt-cli

beecollab_project_setup_npm:
  npm.bootstrap:
    - name: {{ common['project_root'] }}/src/collective.rcse/collective/rcse/resources/dev/
    - user: {{ common['user'] }}
{% endif %}

beecollab_project_setup:
  cmd.run:
    - name: grunt
    - cwd: {{ common['project_root'] }}/src/collective.rcse/collective/rcse/resources/dev/
    - user: {{ common['user'] }}
{% endmacro %}

{% macro install_ode_api_project() %}
{% do kwargs.setdefault('url', 'ssh://git@gitorious.makina-corpus.net/beecollab/beecollab.git') -%}
{% do kwargs.setdefault('name', 'beecollab') -%}
{% do kwargs.setdefault('user', 'beecollab') -%}
{% do kwargs.setdefault('domain', 'beecollab.makina-corpus.net') -%}
{% do kwargs.setdefault('sls_includes', [
  'makina-states.localsettings.nodejs',
  ]) -%}

{% set common = salt['mc_project.get_common_vars'](*varargs, **kwargs) -%}

{{ install_dependancies(common) }}
{{ install_zope(common, *varargs, **kwargs) }}
{{ install_etherpad(common) }}
{{ install_setup(common) }}
{% endmacro %}
