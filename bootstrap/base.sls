#
# Basic bootstrap is responsible for the pre-setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the BOX as it is a "bootstrap stage".
#
# We just ensure is consuming states to tag the machine for its usage
#

include:
  - makina-states.setups.base

