{#-
# This states file aims to configure and manage the base structure for
# astrailssafe/safe backup system
# See https://github.com/astrails/safe
#
# NOTE:
#   - This was a try to use this application and is not maintained anymore.
#   - The only usefulness of this state at the moment is that it is an*
#     exemple on how to use the rvmapp project macro.
#}

{% macro do(full=True) %}
{%- import "makina-states/projects/1/rvmapp.jinja" as rvmapp with context %}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.astrailssafe') }}
{# add to rvm group #}
astrailssafe-add-db-backup-to-rvm:
  user.present:
    - name: db-backup
    - remove_groups: False
    - optional_groups:
      - rvm

{{- rvmapp.install_rvm_app(name='astrailssafe',
                          url='https://github.com/makinacorpus/safe.git',
                          project_root=locs.apps_dir+'/astrailssafe',
                          sls_includes=['makina-states.services.backup.users'],
                          user='db-backup',
                          no_reset_perms=True,
                          no_default_includes=True,
                          no_salt=True,
                          no_domain=True) }}

{% endmacro %}
{{ do(full=False) }}
