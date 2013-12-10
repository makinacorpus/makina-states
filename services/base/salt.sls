#
# Salt base installation
# We set
#   - salt root in /srv/salt
#   - salt conf in /etc/salt
#   - pillar in /srv/pillar
#   - projects code source is to be managed in /srv/projects
#
# This state file only install a minion
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
#
{% import "makina-states/_macros/salt.jinja" as c with context %}
{% set name='salt' %}
{% set mode='salt' %}
{{ c.install_makina_states(name, mode)}}
{{ c.install_makina_states_minion(name, mode)}}
