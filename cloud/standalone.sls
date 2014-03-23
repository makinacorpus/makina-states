{#-
# Services are the centric and last part of our installations, and the final gold goal
#
# This file aims to enable the autoinclusion mecanism to load all the
# already registered cloud drivers & controllers and those one which are configured to be runned
# via then pillar or via grains (see ../top.sls)
#
# We let the user have a word on the final local settings which are activated
# This can be customized by putting keys either in pillar or in grains
# in the form: 'makina-states.services.<statename>'
#
# EG: to disable saltify
#
#  makina-states.cloud.saltify:  False
#}
{{ salt['mc_macros.autoinclude'](salt['mc_cloud.registry']()) }}
