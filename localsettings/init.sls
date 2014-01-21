{#-
# Settings and local configuration to apply to a minion
# For example; writing something in /etc is a good catch for a localsettings states
#
# Take a look to the _macros/localsettings.jinja to have an overview of what is enabled by default
#
# We let the user have a word on the final local settings which are activated
# This can be customized by putting keys either in pillar or in grains
# in the form: 'makina-states.localsettings.<statename>'
#
# EG: to disable the default vim configuration, either set a grain or a pillar value:
#
#  makina-states.localsettings.vim: False
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ localsettings.autoinclude() }}
