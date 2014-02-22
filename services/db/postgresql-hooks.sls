{#-
# Hooks to attach to for orchestration purpose in postgresql states
# - We create in order:
#   - groups
#   - databases
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
{%- set postinst = 'makina-postgresql-post-inst' %}
{{services.funcs.proxy(prebase)}}
{{services.funcs.proxy(postbase, '''
    - watch:
      - mc_proxy: {0}
'''.format(prebase))}}
{{services.funcs.proxy(postinst, '''
    - watch:
      - mc_proxy: {0}
      - mc_proxy: {1}
'''.format(postbase, prebase))}}
{%- set orchestrate = {
  'base': {'prebase': prebase,
           'postinst': postinst,
           'postbase': postbase}
  } %}
{%- for ver in services.pgVers %}
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
}) %}
{{services.funcs.proxy(pregroup, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(postbase, postinst))}}
{{services.funcs.proxy(postgroup)}}
{{services.funcs.proxy(predb, '''
    - watch:
      - mc_proxy: {0}
      - mc_proxy: {1}
    - watch_in:
      - mc_proxy: {2}
'''.format(postbase, postgroup, postinst))}}
{{services.funcs.proxy(postdb)}}
{{services.funcs.proxy(preuser, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(postbase, postinst))}}
{{services.funcs.proxy(postuser)}}
{% endfor %}
