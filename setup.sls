# The setup of makina-states is responsible for
# installing and keeping up & running the base salt infrastructure
#
# It will look in pillar & grains which bootstrap to apply.
# Indeed, at bootstrap stage, we had set a grain to tell which one we had
# run and we now have enougth context to know how and what to upgrade.
# So, this setup state will at least extend the used boostrap state.
#
# - Steps of updating makina-states
#   - Update code
#   - Maybe Re buildout bootstrap & buildout which update some other
#     parts of the code and install new core python libraries & scripts
#   - Install base system prerequisites & configuration
#   - Install salt/mastersalt infrastructure & base pkgs
#   - Take care of file mode and ownership deployed by salt (see below)
#
{% import "makina-states/_macros/salt.jinja" as c with context %}

include:
  - makina-states.servers.base
