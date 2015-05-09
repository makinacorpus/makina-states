# This comes from a bare MakinaStates LXC Tarball
# and transforms it on a shiny systemd enabled container
FROM makinacorpus/makina-states-docker:vivid
ADD  init.sh /init.sh
ADD  systemd.sh /systemd.sh
RUN chmod +x /init.sh /systemd.sh
CMD  ["/init.sh", "systemd.log_level=debug", "systemd.log_target=console"]
