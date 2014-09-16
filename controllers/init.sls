{#-
# Controllers are responsible for applying and deploying all the configuration
# and act as a slave for us to control the nodetypes to run our settings & services
#
# This file aims to enable the autoinclusion mecanism to load all the
# already registered services and those one which are configured to be runned
# via then pillar or via grains (see ../top.sls)
#
# We let the user have a word on the final local settings which are activated
# This can be customized by putting keys either in pillar or in grains
# in the form: 'makina-states.controllers.<statename>'
#
# EG: to disable the mastersalt_master
#
#  makina-states.controllers.mastersalt_master: False
#}
{{ salt['mc_macros.autoinclude'](salt['mc_controllers.registry']()) }}
  - makina-states.common.autocommit
