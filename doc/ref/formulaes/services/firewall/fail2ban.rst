fail2ban configuration
========================
Configure fail2ban, see the salt :ref:`module_mc_fail2ban` module to know which option to configure in pillar.

Pillar key: **makina-states.services.firewall.fail2ban**

Eg::

  makina-states.services.firewall.fail2ban: true
  makina-states.services.firewall.fail2ban.maxretry: 10



