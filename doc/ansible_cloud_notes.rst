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


Cooking and delivery of container / container templates
--------------------------------------------------------
Initialise a lxc container that will be the base of our image (after creation go edit
in it until sastified of the result)::

  ANSIBLE_TARGETS="$controller,lxc$vm_tmpl" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=lxc$vm_tmpl"

Synchronise it to an offline image, this will copy the container to the image,
and remove parts from it (like sshkeys) to impersonate it::

  ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
    ansible/plays/cloud/snapshot_container.yml -e "lxc_template=$vm_tmpl lxc_container_name=lxc$vm_tmpl"

Arguments:

    ANSIBLE_TARGETS
        compute node where the container resides (must be in ansible inventary)
    lxc_template
        lxc image to create
    lxc_container_name
        lxc container which serve as a base for the image

Transfer the template to the compute node where you want to spawn containers
from that image::

   ANSIBLE_TARGETS="$cn,$controller" bin/ansible-playbook \
    ansible/plays/cloud/sync_container.yml -e "lxc_host=$cn lxc_orig_host=$controller lxc_container_name=$vm_tmpl"

Arguments:

    ANSIBLE_TARGETS
        both orig and dest
    lxc_host
        where to transfer container/template
    lxc_orig_host
        where from transfer container/template
    lxc_container_name
        lxc container to transfer

Initialise a container
-----------------------
Initialise and finish the container provisioning (from scratch)::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=$vm"

Arguments:

    ANSIBLE_TARGETS
        compute node where the container resides (must be in ansible inventary)
    lxc_container_name
        lxc container to create

Initialise and finish the container provisioning (from template)::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=$vm lxc_from_container=$vm_tmpl"

Arguments:

    ANSIBLE_TARGETS
        compute node where the container resides (must be in ansible inventary)
    lxc_template
        lxc image to create
    lxc_from_container
        lxc container from which initing the container




