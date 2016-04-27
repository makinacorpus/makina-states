Create lxc containers in a cloud
===================================
workflow:

Go into makina-states folder::

    cd /srv/makina-states

Edit database::

    vim etc/makina-states/database.sls

Define shell variable to copy/paste following commands::

    export controller="$(hostname -f)"
    export cn="$(hostname -f)"
    # export cn="c.foo.net"
    export vm="d.foo.net"
    export vm_tmpl="makinastates"

Preparation on the controller
-----------------------------
Refresh cache::

  # bin/salt-call -lall state.sls makina-states.services.cache.memcached # the first time
  service memcached restart
  _scripts/refresh_makinastates_pillar.sh
  # or with limit on hosts that the run will be
  ANSIBLE_TARGETS="$controller,$vm,$cn" _scripts/refresh_makinastates_pillar.sh

Preinstalling makina-states (controller & each compute node)
-----------------------------------------------------------------
Installing it::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/makinastates/install.yml

Or on a makina-states v1 node, unwire old ms and install msv2::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/makinastates/migv2.yml


Configure the dns on a full makina-states infra with mc_pillar
--------------------------------------------------------------
::

  ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
    ansible/plays/cloud/controller.yml


Compute node related part
----------------------------
Configure compute_node with::

  ANSIBLE_TARGETS="$cn" ansible-playbook \
    ansible/plays/cloud/compute_node.yml


Cooking and delivery of container templates
---------------------------------------------------
Initialise a lxc container image and snapshot with with (after creation go edit
until complete the container)::

  ANSIBLE_TARGETS="$controller,lxc$vm_tmpl" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=lxc$vm_tmpl"

Synchronise it to an offline image, this will copy the container to the image,
and remove parts from it (like sshkeys) to impersonate it::

  ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
    ansible/plays/cloud/snapshot_container.yml -e "lxc_template=$vm_tmpl lxc_container_name=lxc$vm_tmpl"

Transfer the template to the compute node where you want to spawn containers
from that image::

   ANSIBLE_TARGETS="$cn,$controller" bin/ansible-playbook \
    ansible/plays/cloud/sync_container.yml -e "lxc_host=$cn lxc_orig_host=$controller lxc_container_name=$vm_tmpl"

Initialise a container
-----------------------
Initialise and finish the container provisioning (from scratch)::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=$vm"

Initialise and finish the container provisioning (from template)::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=$vm from_container=$vm_tmpl"
