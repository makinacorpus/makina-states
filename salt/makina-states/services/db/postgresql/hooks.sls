{#-
# Hooks to attach to for orchestration purpose in postgresql states
# - We create in order:
#   - groups
#   - databases
#   - users
#}

include:
  - makina-states.localsettings.ssl.hooks

{% macro proxy(name, text='') %}
{{name}}:
  mc_proxy.hook:
    - name: {{name}}
{{text}}
{% endmacro %}
{%- set settings = salt['mc_pgsql.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set default_user = settings.user %}
{%- set orchestrate = {} %}
{%- set prebase = 'makina-postgresql-pre-base' %}
{%- set postbase = 'makina-postgresql-post-base' %}
{%- set prepkg = 'makina-postgresql-pre-pkg' %}
{%- set postpkg = 'makina-postgresql-post-pkg' %}
{%- set presetup = 'makina-postgresql-presetup' %}
{%- set postinst = 'makina-postgresql-post-inst' %}
{{proxy(prebase)}}
{{proxy(postbase, '''
    - watch:
      - mc_proxy: {0}
'''.format(prebase))}}
{{proxy(prepkg, '''
    - watch:
      - mc_proxy: {0}
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: {1}
'''.format(prebase, presetup))}}
{{proxy(postpkg, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(prepkg, presetup))}}
{{proxy(presetup, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(postpkg, postbase))}}
{{proxy(postinst, '''
    - watch:
      - mc_proxy: {0}
      - mc_proxy: {1}
'''.format(postbase, prebase))}}
{%- set orchestrate = {
  'base': {'prebase': prebase,
           'prepkg': prepkg,
           'postpkg': postpkg,
           'presetup': presetup,
           'postinst': postinst,
           'postbase': postbase}
  } %}
{%- for ver in settings.versions %}
{%- set pregroup = ver+'-makina-postgresql-pre-create-group' %}
{%- set postgroup = ver+'-makina-postgresql-post-create-group' %}
{%- set predb = ver+'-makina-postgresql-pre-create-db' %}
{%- set postdb = ver+'-makina-postgresql-post-create-db' %}
{%- set preuser = ver+'-makina-postgresql-pre-create-user' %}
{%- set postuser = ver+'-makina-postgresql-post-create-user' %}
{%- set prefixowner = ver+'-makina-postgresql-pre-fix-owner' %}
{%- set postfixowner = ver+'-makina-postgresql-post-fix-owner' %}
{%- do orchestrate.update({ver: {} }) %}
{%- do orchestrate[ver].update({
  'pregroup': pregroup,
  'postgroup': postgroup,
  'predb': predb,
  'postdb': postdb,
  'preuser': preuser,
  'postuser': postuser,
  'prefixowner': prefixowner,
  'postfixowner': postfixowner,
}) %}
{{proxy(pregroup, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(postbase, postinst))}}
{{proxy(postgroup)}}
{{proxy(predb, '''
    - watch:
      - mc_proxy: {0}
      - mc_proxy: {1}
    - watch_in:
      - mc_proxy: {2}
'''.format(postbase, postgroup, postinst))}}
{{proxy(postdb)}}
{{proxy(preuser, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(postbase, postinst))}}
{{proxy(postuser)}}
{{proxy(prefixowner, '''
    - watch:
      - mc_proxy: {0}
    - watch_in:
      - mc_proxy: {1}
'''.format(postuser, postinst))}}
{{proxy(postfixowner)}}
{% endfor %}

pgsql-service-restart-hook:
  mc_proxy.hook: []

