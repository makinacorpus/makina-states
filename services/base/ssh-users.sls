{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}

include:
  - makina-states.localsettings.users
  - makina-states.services.base.ssh-hooks

{%- for user, keys_info in localsettings.user_keys.items() %}
{%-  for commentid, keys in keys_info.items() %}
{%-    for key in keys %}
ssh_auth-{{ user }}-{{ commentid }}-{{ key }}:
  ssh_auth.present:
    - comment: key for {{ commentid }}
    - user: {{ user }}
    - source: salt://files/ssh/{{ key }}
    - require_in:
      - mc_proxy: ssh-post-user-keys
    - require:
      - user: {{ user }}
{%-    endfor %}
{%-  endfor %}
{%- endfor %}
