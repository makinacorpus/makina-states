{#- Common php installations (mod_php or php-fpm) files #}
{# TODO: install suhoshin on Debian #}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{% set phpSettings = salt['mc_php.settings']() %}
{% set s_ALL = phpSettings.s_ALL %}
{% set apacheSettings = salt['mc_apache.settings']() %}
{% set apache = False %}

{% macro includes(full=True, apache=False) %}
  {% if full -%}
  {%  if grains.get('lsb_distrib_id','') == "Debian" -%}
  {# Include dotdeb repository for Debian #}
  - makina-states.localsettings.repository_dotdeb
  {%-  endif %}
  {%- endif %}
  {%  if full %}
  - makina-states.services.php.real-common
  {%  else %}
  - makina-states.services.php.real-common-standalone
  {%-  endif %}
  - makina-states.services.php.php-hooks
  {% if apache -%}
  - makina-states.services.php.php-apache-hooks
  {%  if full %}
  - makina-states.services.http.apache
  {%  else %}
  - makina-states.services.http.apache-standalone
  {%-  endif %}
  {%- endif %}
{% endmacro %}

{% macro common_includes(full=True, apache=False) %}
{% if full %}
  {% if apache %}
  - makina-states.services.php.common_with_apache
  {% else %}
  - makina-states.services.php.common
  {% endif %}
{% else %}
  {% if apache %}
  - makina-states.services.php.common_with_apache-standalone
  {% else %}
  - makina-states.services.php.common-standalone
  {% endif %}
{% endif %}
{% endmacro %}

{% macro do(full=True, apache=False) %}
{% if apache and full %}
{%  if grains.get('lsb_distrib_id','') == "Debian" %}
dotdeb-apache-makina-apache-php-pre-inst:
  mc_proxy.hook:
    - require:
      - pkgrepo: dotdeb-repo
    - watch_in:
      - mc_proxy: makina-apache-php-pre-inst
{%  endif %}
{% endif %}
{% endmacro %}

include:
{{ includes(full=False, apache=false) }}
{{ do(full=False, apache=false) }}
