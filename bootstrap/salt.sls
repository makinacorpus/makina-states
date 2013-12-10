#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.bootstrap.base
  - makina-states.services.base.salt
  - makina-states.services.base.salt_master
