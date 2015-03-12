Configuration
=============

Makina states is a consistent collection of states (or formulaes) that you just
have to apply on your system to install and configure a particular services.
To configure a machine and its underlying services via makina-states,
we use registries which will feed their exposed variables through different
configuration sources where the main ones are the grains and the pillar
and the local makina-states registries.

To install something, you can either:

  - set a key/value in pillar or grains (eg: **makina-states.services.http.nginx true**)
  - Call directly a specific state: **salt-call state.sls makina-states.services.http.nginx**
  - Include directly a specific state in a **include:** sls statement

As soon as those tags are run, they will set a grain on the machine having
the side effect to register that set of states to be 'auto installed'
and 'reconfigured' on next highstates, implicitly.
In other word, in the future highstates, they will even run even
if we have not included them explicitly.
To sum up, we have made all of those states reacting and setting tags for the system
to be totally dynamic. All the things you need to do is to set in pillar or in grains
the appropriate values for your machine to be configured.

In other words, you have 4 levels to make salt install you a 'makina state'
which will be automaticaly included in the next highstate:

  - Direct inclusion via the 'include:' statement::

        foo.sls:
            include:
              - include makina-states.services.http.nginx

  - Install directly the state via a salt/salt-call state.sls::

      salt-call state.sls makina-states.services.http.nginx

  - Relevant grain configuration slug::

      salt-call --local grains.setval makina-states.services.http.nginx true
      salt-call state.highstate

  - Relevant pillar configuration slug::

      /srv/pillar/foo.sls
      makina-states.services.http.nginx: true in a pillar file

  - Run the highstate, and as your machine is taggued,nginx will be installed

You can imagine that there a a lot of variables that can modify the configurationa applied to a minion.
To find what to do, we invite you to just read the states and the documentation that seem to be relevant to your needs.

Best practise
--------------
Be careful with grains
~~~~~~~~~~~~~~~~~~~~~~
As grains are particulary insecures because they are freely set on the client (minion) side,
pay attention that states and pillar accesses chained by this inheritance are only
limited to the scope you want and do not expose too many sensitive information.

To better understand how things are done, this is an non exhaustive graph
or our states tree:

Writing rules
~~~~~~~~~~~~~~

Some rules to write makina-states states:

  - When you create a new state, include it in its respective registry.
  - Never ever write an absolute path, use localsettings.locations.PATH_PREFIX
    or another registry variable.
  - Try to isolate the settings and make a subregistry to regroup them.
  - Never ever use short form of states (states without names, use states unique IDs)

    DO::

        foo-foo:
            cmd.run
                name: /foo/foo

    DONT::

        /foo/foo
            cmd.run: []


  - Please use as much as possible require(_in)/watch(_in) to ensure your configuration
    slugs will be correctly scheduled
  - If your states are getting being or need scheduling, please add separate hooks files (see developer documentation).


Organize your pillar
----------------------
Global part for minions
~~~~~~~~~~~~~~~~~~~~~~~~~
You can make your pillar management far more easier by making an automatic 'per kind machine picking' pillar::

/srv/{mastersalt-}salt/top.sls

::

    {%- set mastersalt = 'hosting-idmachine.company.net' %}
    {%- set pillar_root = opts['pillar_roots']['base'][0] %}
    {%- set minions_root = 'minions' %}
    base:
      '*':
        {# the minimal info for mastersalt minions  #}
        {# please never add more here that the bare #}
        {# minimum for running a mastersalt minion  #}
        - mastersalt_minion
      {# do not put the variable as it is grepped in boot-salt #}
      'hosting-idmachine.company.net':
        - custom
        {# the local for mastersalt master pillar file, this must stay here for boot-salt.sh #}
        - mastersalt
        - minions.bm.hosting-idmachine+company+net
    {%- macro pillar_include(minions_kind) %}
    {%- set mfull_dir = '{0}/{1}'.format(minions_root, minions_kind) %}
    {%- set full_dir = '{0}/{1}'.format(pillar_root, mfull_dir) %}
    {%- for sls in salt['file.readdir'](full_dir) %}
    {%- set name = sls.replace('+', '.')[:-4] %}
    {%   if sls not in ['.', '..'] and sls.endswith('.sls') and not mastersalt in name %}
      '{{name}}':
        - {{mfull_dir.replace('/', '.')}}.{{sls[:-4]}}
    {%   endif %}
    {% endfor %}
    {% endmacro %}
    {# dynamicly include all found sls in :
        minions/bm
        minions/vm/kvm
        minions/vm/lxc/*/* #}
    {{ pillar_include('bm') }}
    {% for compute_node in salt['file.readdir']('{0}/{1}/{2}'.format(pillar_root, minions_root, 'vm/lxc')) %}
    {{ pillar_include('vm/lxc/{0}'.format(compute_node)) }}
    {% endfor %}
    {{ pillar_include('vm/kvm') }}


Then on the filesystem in /srv/mastersalt-pillar::

    ├── ./minions
    ├── ./minions/bm
    │   ├── ./minions/bm/hosting-idmachine+company+net.sls
    │   └── ./minions/bm/anotherbox+company+net.sls
    └── ./minions/vm
        ├── ./minions/vm/kvm
        │   ├── ./minions/vm/kvm/dev-project1+company+net.sls
        ├── ./minions/vm/lxc
        │   └── ./minions/vm/lxc/anotherbox+company+net
        │       ├── ./minions/vm/lxc/anotherbox+company+net/qa-project2+company+net.sls


Configuration of makina-states related files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We do have something that looks like this, /srv/mastersalt-pillar::

    ./makina-states
    ├── ./makina-states/backup.sls
    ├── ./makina-states/env.sls
    ├── ./makina-states/fail2ban.sls
    ├── ./makina-states/hosts.sls
    ├── ./makina-states/init.sls
    ├── ./makina-states/ips.sls
    ├── ./makina-states/ldap.sls
    ├── ./makina-states/lxc.sls
    ├── ./makina-states/psad.sls
    ├── ./makina-states/security.sls
    ├── ./makina-states/shorewall.sls
    ├── ./makina-states/smtp_relay.sls
    ├── ./makina-states/ssh.sls
    ├── ./makina-states/sysadmins.sls
    ├── ./makina-states/full-nosec.sls
    ├── ./makina-states/full.sls

Try to separate your settings and use includes to make clever pillar agencements.
Idea here is to mimic the makina-states state tree organization.
Then we use the full and full-nosec profiles to aggregate all of those states.

Configuration of the cloud contrroller part
++++++++++++++++++++++++++++++++++++++++++++
Idea is to organise things for:

    - baremetal machines to have their conf to be applied after
    - compute nodes (spetial kind of baremetal) to be registered as saltified machines.
    - lxc or vms to be picked up using the right makina-states profile.

/srv/mastersalt-pillar::

    ./makina-states
    ├── ./makina-states/cloud
    │   ├── ./makina-states/cloud/compute_nodes.sls
    │   ├── ./makina-states/cloud/driver_generic.sls
    │   ├── ./makina-states/cloud/driver_lxc.sls
    │   ├── ./makina-states/cloud/driver_saltify.sls
    │   ├── ./makina-states/cloud/images.sls
    │   ├── ./makina-states/cloud/init.sls
    │   └── ./makina-states/cloud/vms.sls


Due to the pillar organization, we can do some logic to autoload the computes nodes & vms settings.

./makina-states/cloud/init.sls::

    include:
      - makina-states.cloud.driver_generic
      - makina-states.cloud.driver_saltify
      - makina-states.cloud.driver_lxc
      - makina-states.cloud.compute_nodes
      - makina-states.cloud.images
      - makina-states.cloud.vms

makina-states/cloud/compute_nodes.sls::

    {% import "top.sls" as top with context %}
    {% set minions_root = top.minions_root %}
    {% set lxc_dir = "{0}/vm/lxc".format(minions_root) %}
    {% set full_lxc_dir = '{0}/{1}'.format(top.pillar_root, lxc_dir) %}
    {% for encoded_compute_node in salt['file.readdir'](full_lxc_dir) %}
    {% if not encoded_compute_node  in ['.', '..'] %}
    {% set compute_node = encoded_compute_node.replace('+', '.') %}
    {% import "{0}/bm/{1}.sls".format(top.minions_root, encoded_compute_node) as bm with context %}
    makina-states.cloud.saltify.targets.{{compute_node}}:
      password: {{bm.clear_pass}}
      ssh_username: root
    {% endif %}
    {% endfor %}

./makina-states/cloud/driver_*::

    makina-states.cloud.generic: true
    makina-states.cloud.master: mastersalt.company.net
    makina-states.cloud.master_port: 4606
    {# lxc driver #}
    makina-states.cloud.lxc: true
    makina-states.cloud.lxc.defaults.profile: large
    makina-states.cloud.lxc.defaults.backing: lvm
    makina-states.cloud.saltify: true

makina-states/cloud/vms.sls::

    {% import "top.sls" as top with context %}
    {% set minions_root = top.minions_root %}
    {% set lxc_dir = "{0}/vm/lxc".format(minions_root) %}
    {% set full_lxc_dir = '{0}/{1}'.format(top.pillar_root, lxc_dir) %}
    {% for encoded_compute_node in salt['file.readdir'](full_lxc_dir) %}
    {% if not encoded_compute_node  in ['.', '..'] %}
    {% set compute_node = encoded_compute_node.replace('+', '.') %}
    {% set compute_node_dir = '{0}/{1}'.format(lxc_dir, encoded_compute_node) %}
    {% set full_compute_node_dir = '{0}/{1}'.format(full_lxc_dir, encoded_compute_node) %}
    makina-states.cloud.lxc.vms.{{compute_node}}:
    {% for sls in salt['file.readdir'](full_compute_node_dir) %}
    {% if sls.endswith('.sls') %}
    {% import '{0}/{1}'.format(compute_node_dir, sls) as vm %}
    {% set name = sls[:-4].replace('+', '.') %}
      '{{name}}':
        password: '{{vm.clear_pass}}'
        profile: large
        profile_type: lvm
    {% endif %}
    {% endfor %}
    {% endif %}
    {% endfor %}
    makina-states.cloud.lxc.vms.hosting-idmachine.company.net:
      msr-lxc-ref.company.net:
        ip: 10.5.1.2
        password: xxx
        profile_type: dir

./makina-states/cloud/compute_nodes.sls::

    {% import "top.sls" as top with context %}
    {% set minions_root = top.minions_root %}
    {% set lxc_dir = "{0}/vm/lxc".format(minions_root) %}
    {% set full_lxc_dir = '{0}/{1}'.format(top.pillar_root, lxc_dir) %}
    {% for encoded_compute_node in salt['file.readdir'](full_lxc_dir) %}
    {% if not encoded_compute_node  in ['.', '..'] %}
    {% set compute_node = encoded_compute_node.replace('+', '.') %}
    {% import "{0}/bm/{1}.sls".format(top.minions_root, encoded_compute_node) as bm with context %}
    makina-states.cloud.saltify.targets.{{compute_node}}:
      password: {{bm.clear_pass}}
      ssh_username: root
    {% endif %}
    {% endfor %}

An exemple of vm, ./minions/vm/lxc/anotherbox+company+net/qa-project2+company+net.sls::

    {% import "makina-states/variables.sls" as var with context %}
    include:
      - makina-states.full-nosec
    {% set clear_pass='xxx' %}
    {% set pass=salt['mc_utils.unix_crypt'](clear_pass) %}
    makina-states.localsettings.admin.sysadmin_password: {{pass}}
    makina-states.localsettings.admin.sudoers: {{['jmf'] + var.sysadmins }}

An exemple of computenode, minions/bm/anotherbox+makina-corpus+net.sls::

    include:
      - makina-states.lxc
      - makina-states.full
    {% set thishost = 'anotherbox.makina-corpus.net' %}
    {% set thisip = '17.32.21.8' %}
    {% set clear_pass='xxx' %}
    {% set pass=salt['mc_utils.unix_crypt'](clear_pass) %}
    {% set clear2_pass='xxx' %}
    {% set pass2=salt['mc_utils.unix_crypt'](clear_pass2) %}
    makina-states.localsettings.admin.root_password: {{pass}}
    makina-states.localsettings.admin.sysadmin_password: {{pass2}}
    makina-states.localsettings.network.managed: true
    {{thishost}}-makina-network:
      eth0:
        address: {{thisip}}
        netmask: 255.255.255.0
        network: 178.1.1.0
        broadcast: 178.1.1.255
        gateway: 178.1.1.254
        dnsservers: 127.0.0.1 8.8.8.8 4.4.4.4

An exemple of cloudcontroller, ./minions/bm/hosting-idmachine+company+net.sls::

    include:
      - makina-states.cloud
      - makina-states.lxc
      - makina-states.full
    makina-states.controllers.mastersalt_master: true
    makina-states.localsettings.network.managed: true
    {% set clear_pass='xxx'%}
    {% set pass=salt['mc_utils.unix_crypt'](clear_pass) %}
    makina-states.localsettings.admin.sysadmin_password: {{pass}}

TODO:
  - We are planning the uninstall part but it is not yet done
  - In the meantime, to uninstall a state, you ll have first to remove the grain/pillar/inclusion
    Then rerun the highstate and then code a specific cleanup sls file if you want to cleanup
    what is left on the server


