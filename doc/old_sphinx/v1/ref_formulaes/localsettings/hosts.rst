/etc/hosts managment
=====================
Configure /etc/hosts entries based on configuration setings:

Eg having in pillar
.. code-block:: yaml

    toto-makina-hosts:
        - ip: 10.0.0.8
          hosts: foo.company.com foo
        - ip: 10.0.0.3
          hosts: bar.company.com bar
    others-makina-hosts:
        - ip: 192.168.1.52.1
          hosts: foobar.foo.com foobar
        - ip: 192.168.1.52.2
          hosts: toto.foo.com toto2.foo.com toto3.foo.com toto
        - ip: 10.0.0.4
          hosts: alias alias.foo.com


All theses entries will be entered inside a block identified by
.. code-block:: yaml

     #-- start salt managed zone -- PLEASE, DO NOT EDIT
     (here)
     #-- end salt managed zone --

It's your job to ensure theses IP will not be used on other
entries in this file.

If you want to add some data in this block without using the pillar
you can also use a file.accumulated state and push content in
an accumulator while targeting /etc/hosts file with filename entry,
this way
.. code-block:: yaml

     this-is-my-custom-state
        file.accumulated:
          - filename: /etc/hosts
          - name: hosts-accumulator-makina-hosts-entries
          - text: "here your text"
          - require_in:
            - file: makina-etc-host-vm-management


