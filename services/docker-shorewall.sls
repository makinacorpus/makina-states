#
# LXC and shorewall integration, be sure to add
# docker guests to shorewall running state
# upon creation
# A big sentence to say, restart shorewall
# after each docker creation to enable
# the container network
#
include:
  - makina-states.services.shorewall
  - makina-states.services.docker

extend:
  docker-post-inst:
    cmd.run:
      - watch_in:
        - cmd: shorewall-restart

