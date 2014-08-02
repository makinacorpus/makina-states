{#-
# Services managers are the ones which managers services
#  makina-states.services.mysql:  False
#}
{{ salt['mc_macros.autoinclude'](salt['mc_services_managers.registry']()) }}
