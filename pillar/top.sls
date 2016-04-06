{# This is the top pillar configuration file, link here all your
 # environment configurations files to their respective minions #}
{#- autoloading pillar in each <pillar root>/pillar.d directory
   the main uses by now is:
     - load makina-states mc_project based projects local configurations
     - load makina-states masterless configuration (m_pillar

The linking cannot be done as an ext-pillar as the static files rendered
order is not guarranteed, we need so to wrap that here
#}

{%- set top = {} %}
{%- if not opts.get('no_makinastates_autoload', False) %}
{%-   set autotop = salt['mc_macros.get_pillar_top_files'](
        pillar_autoincludes=True,
        mc_projects=True,
        refresh_projects=True) %}
{%-   for section, aslss in autotop.items() %}
{%-     for sls in aslss %}
{%-       set slss = top.setdefault(section, []) %}
{%-       if sls not in slss %}{% do slss.append(sls) %}{% endif %}
{%-     endfor %}
{%-   endfor %}
{%- endif %}
base:
  {% if top %}
  {% for section, slss in top.items() %}
  '{{section}}':
    {% for sls in slss %}
    - {{ sls }}
    {% endfor %}
  {% endfor %}
  {% else %}
  not_trigger_render_errors: []
  {% endif %}
