#
# Nodetypes are the PiceOfHarware or VM we are installing our softwares onto.
#
# This file aims to enable the autoinclusion mecanism to load all the
# already registered services and those one which are configured to be runned
# via then pillar or via grains (see ../top.sls)

# Take a look to the _macros/nodetypes.jinja to have an overview of what is enabled by default
#
# We let the user have a word on the final local settings which are activated
# This can be customized by putting keys either in pillar or in grains
# in the form: 'makina-states.nodetypes.<statename>'
#
# EG: to disable the default configuration applied on a vagrantvm
#
#  makina-states.nodetypes.vagrantvm: False
#

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ nodetypes.autoinclude() }}
