{% set msr = '/srv/salt/makina-states' %}
{% set group = pillar.get('salt.filesystem.group', 'editor') %}
{% set resetperms = "file://"+msr+"/_scripts/reset-perms.sh" %}
{% set group_id = pillar.get('salt.filesystem.gid', 65753) %}
{% set rotate = pillar.get('salt.rotate', '31') %}
{% set saltbinpath = msr+'/bin' %}

{% set vm = salt['config.get']('makina.bootstrap.vm', False) %}
{% set server = salt['config.get']('makina.bootstrap.server', False) %}
{% set sa = salt['config.get']('makina.bootstrap.standalone', False) %}

{% set ms = salt['config.get']('makina.bootstrap.mastersalt', False) -%}
{% set mmaster = salt['config.get']('makina.mastersalt-master', False) %}
{% set mminion = salt['config.get']('makina.mastersalt-minion', False) %}

{% set master = salt['config.get']('makina.salt-master', False) %}
{% set minion = salt['config.get']('makina.salt-minion', False) %}

{% set mastersalt = mmaster or mminion or ms %}
{% set no_bootstrap = not (vm or server or sa or ms) %}
{% set salt_enabled = vm or server or master or minion or mastersalt %}


