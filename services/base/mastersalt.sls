# As described in wiki each server has a local master
# but can also be controlled via the mastersalt via the syndic interface.
# We have the local master in /etc/salt
# We have the running syndic/master/minion in /etc/salt
# and on mastersalt, we have another master daemon configured in /etc/mastersalt

{% import "makina-states/_macros/salt.jinja" as c with context %}
include:
  - makina-states.services.base.salt

{{ set name='mastersalt' }}
{{ set mode='mastersalt' }}
{{ install_makina_states(name, mode)}}
{{ install_makina_states_minion(name, mode)}}
