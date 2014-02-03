{#-
# Hooks to attach to for orchestration purpose in postgresql states
# - We create in order:
#   - groups
#   - databases
#   - extensions
#   - users
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set services = services %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = localsettings.locations %}
{%- set default_user = services.postgresqlUser %}
{%- set orchestrate = {} %}
{%- set prebase = 'makina-postgresql-pre-base' %}
{%- set postbase = 'makina-postgresql-post-base' %}
{{services.funcs.dummy(prebase)}}
{{services.funcs.dummy(postbase)}}
{%- set orchestrate = {
  'base': {'prebase': prebase,
           'postbase': postbase}
  } %}
{%- for ver in services.pgVers %}
{%- set preext = ver+'-makina-postgresql-pre-create-ext' %}
{%- set postext = ver+'-makina-postgresql-post-create-ext' %}
{%- set pregroup = ver+'-makina-postgresql-pre-create-group' %}
{%- set postgroup = ver+'-makina-postgresql-post-create-group' %}
{%- set predb = ver+'-makina-postgresql-pre-create-db' %}
{%- set postdb = ver+'-makina-postgresql-post-create-db' %}
{%- set preuser = ver+'-makina-postgresql-pre-create-user' %}
{%- set postuser = ver+'-makina-postgresql-post-create-user' %}
{%- do orchestrate.update({ver: {} }) %}
{%- do orchestrate[ver].update({
  'pregroup': pregroup,
  'postgroup': postgroup,
  'predb': predb,
  'postdb': postdb,
  'preuser': preuser,
  'postuser': postuser,
  'preext': preext,
  'postext': postext,
}) %}
{{services.funcs.dummy(pregroup, '''
    - require:
      - mc_proxy: {0}
'''.format(postbase))}}
{{services.funcs.dummy(postgroup)}}
{{services.funcs.dummy(predb, '''
    - require:
      - mc_proxy: {0}
      - mc_proxy: {1}
'''.format(postgroup, postbase))}}
{{services.funcs.dummy(postdb)}}
{{services.funcs.dummy(preuser, '''
    - require:
      - mc_proxy: {0}
      - mc_proxy: {1}
'''.format(postdb, postbase))}}
{{services.funcs.dummy(postuser)}}
{{services.funcs.dummy(preext, '''
    - require:
      - mc_proxy: {0}
      - mc_proxy: {1}
'''.format(postdb, postbase))}}
{{services.funcs.dummy(postext)}}
{% endfor %}

