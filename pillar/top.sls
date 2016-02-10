{# This is the top pillar configuration file, link here all your
 # environment configurations files to their respective minions #}
{#- autoloading pillar in each <pillar root>/pillar.d directory
   the main uses by now is:
     - load makina-states mc_project based projects local configurations
     - load makina-states masterless configuration (m_pillar

The linking cannot be done as an ext-pillar as the static files rendered
order is not guarranteed, we need so to wrap that here
#}
{%- set slss = [] %}
{%- if not opts.get('no_makinastates_autoload', False) %}
{%- for sls in salt['mc_macros.get_pillar_top_files'](
      pillar_autoincludes=True,
      mc_projects=True,
      refresh_projects=True) %}
      {% if sls not in slss %}{% do slss.append(sls) %}{% endif %}
{%-  endfor %}
{%- endif %}
base:
  {% if slss %}
  '*':
    {% for sls in sls %}
    - {{ sls }}
    {%endfor %}
  {% else %}
  not_trigger_render_errors: []
  {% endif %}
