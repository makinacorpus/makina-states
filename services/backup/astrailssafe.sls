{#-
# This states file aims to configure and manage the base structure for
# astrailssafe/safe backup system
# See https://github.com/astrails/safe
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- import "makina-states/projects/rvmapp.jinja" as rvmapp with context %}
{%- set services = services %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = localsettings.locations %}
{{- services.register('backup.astrailssafe') }}
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
