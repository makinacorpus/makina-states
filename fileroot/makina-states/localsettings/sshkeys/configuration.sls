include:
  - makina-states.localsettings.sshkeys.hooks

{% set locs = salt['mc_locations.settings']() %}
{% set usergroup = salt['mc_usergroup.settings']() %}
{% macro manage_user_ssh_keys(id, udata=None) %}
{%- if not udata %}{%- set udata = {} %}{%endif%}
{%- set ssh_keys = udata.setdefault('ssh_keys', []) %}
{%- set ssh_absent_keys = udata.setdefault('ssh_absent_keys', []) %}
{%- set home = salt['mc_usergroup.get_home'](id) %}

{% if ssh_absent_keys %}
{% for rkeydata in udata['ssh_absent_keys'] %}
{% for key, data in rkeydata.items() %}
{% set encs = data.get('encs', ['ed25519', 'ecdsa', 'ssh-rsa', 'ssh-ds']) %}
{% for enc in encs %}
ssh_auth-absent-key-{{id}}-{{key}}-{{loop.index0-}}-ssh-keys:
  ssh_auth.absent:
    - name: '{{key}}'
    - user: {{id}}
    - enc: {{enc}}
    {% for opt in ['options', 'config'] %}
    {% if opt in data %}- {{opt}}: {{data[opt]}}{%endif%}
    {% endfor %}
    - watch:
      - mc_proxy: localsettings-ssh-keys-pre
    - watch_in:
      - mc_proxy: localsettings-ssh-keys-post
{%    endfor %}
{%    endfor %}
{%    endfor %}
{% endif %}

{% if ssh_keys %}
ssh_{{id}}-auth-key-cleanup-ssh-keys:
  file.absent:
    - names:
      {#- {{home}}/.ssh/authorized_keys#}
      {# we do not implicitly remove access, harmful #}
      - {{home}}/.ssh/authorized_keys2
    - watch:
      - mc_proxy: localsettings-ssh-keys-pre
    - watch_in:
      - mc_proxy: localsettings-ssh-keys-post
{% for key in ssh_keys %}
{% if key.endswith('.pub') and '/files/' in key %}
ssh_auth-key-{{id}}-{{key-}}-ssh-keys:
{% else%}
ssh_auth-key-{{id}}-keys-{{loop.index0}}-ssh-keys:
{% endif %}
  ssh_auth.present:
    - user: {{id}}
    {% if key.endswith('.pub') and '/files/' in key %}
    - source: {{key}}
    {% else%}
    - name: '{{key}}'
    {% endif %}
    - require:
      - file: ssh_{{id}}-auth-key-cleanup-ssh-keys
    - watch:
      - mc_proxy: localsettings-ssh-keys-pre
    - watch_in:
      - mc_proxy: localsettings-ssh-keys-post
{% endfor %}
{% endif %}
{% endmacro %}

{% for id, udata in usergroup.users.items() %}
{{ manage_user_ssh_keys(id, udata) }}
{% endfor %}
