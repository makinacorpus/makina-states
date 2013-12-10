#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#
{% set devhost = grains.get('makina.devhost', False) %}

{% set includes=[]%}
{% if devhost %}
{% set dummy=includes.append('makina-states.bootstrap.vm') %}
{% endif %}

{% if includes %}
{% for i in includes %}
include:
  - {{i}}
{% endfor %}
{% endif %}
