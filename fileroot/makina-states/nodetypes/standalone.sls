{#-
# Nodetypes are the PiceOfHarware or VM we are installing our softwares onto.
#
# This file aims to enable the autoinclusion mecanism to load all the
# already registered services and those one which are configured to be runned
# via then pillar or via grains (see ../top.sls)

# We let the user have a word on the final local settings which are activated
# This can be customized by putting keys either in pillar or in grains
# in the form: 'makina-states.nodetypes.<statename>'
#
# EG: to disable the default configuration applied on a vagrantvm
#
#  makina-states.nodetypes.vagrantvm: False
#} 

include:
{% for n in salt['mc_nodetypes.get_nodetypes']() %}
  - makina-states.nodetypes.{{n}}
{% endfor %}
