#
# Salt base installation
# We set
#   - file_root: /srv/salt
#   - pillarRoot: /srv/pillar
#   - conf: /etc/salt
#   - projects code source: /srv/projects
#   - sockets: /var/run/{master, minion}
#   - logs: /var/logs/salt/{master, minion}(key*)
#   - services: salt-minon & salt-master
#
# binaries:
#   - /usr/bin/salt
#   - /usr/bin/salt-key
#   - /usr/bin/salt-call
#   - /usr/bin/salt-master
#   - /usr/bin/salt-minion
#
# This state file only install a minion
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
#
#
# Base server which acts also as a mastersalt master
#
{% import "makina-states/_macros/controllers.jinja" as controllers with context %}

{% set oname = 'salt' %}
{% set name = oname+'_minion' %}
{% set saltmac = controllers.saltmac %}
{% set localsettings = controllers.localsettings %}
{{ controllers.register(oname) }}
{{ controllers.register(name) }}

include:
  - {{ controllers.funcs.statesPref }}localsettings

{{ saltmac.install_minion(saltmac.saltname) }}
{{ saltmac.install_makina_states(saltmac.saltname) }}

