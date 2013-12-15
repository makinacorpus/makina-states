#
# Base server which acts also as a salt master
#
include:
  - makina-states.servers.salt_minion
  - makina-states.setups.salt_master

