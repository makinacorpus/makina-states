Create lxc containers in a cloud
===================================
workflow:

Go into makina-states folder::

    cd /srv/makina-states

Edit database::

    vim etc/makina-states/database.sls

Define shell variable to copy/paste following commands::

    export controller="a.foo.net"
    export cn="c.foo.net"
    export vm="d.foo.net"
    export vm_tmpl="makinastates"

Refresh cache::

  service memcached restart
  _scripts/refresh_makinastates_pillar.sh
  # or with limit on hosts that the run will be
  ANSIBLE_TARGETS="$controller,$vm,$cn" _scripts/refresh_makinastates_pillar.sh

Install controller/dns with::

  ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
    ansible/plays/cloud/controller.yml

Preinstall makina-states on compute_node with::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/makinastates/install.yml

Or on a makina-states v1 node, unwire old ms and install msv2::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/makinastates/migv2.yml

Configure compute_node with::

  ANSIBLE_TARGETS="$cn" ansible-playbook \
    ansible/plays/cloud/compute_node.yml

(opt) Prepare a lxc container image and snapshot with with
::

  ANSIBLE_TARGETS="$controller,lxc$vm_tmpl" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=lxc$vm_tmpl"

(opt) Synchronise it to an offline image::

::

  ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
    ansible/plays/cloud/snapshot_container.yml -e "lxc_template=$vm_tmpl lxc_container_name=lxc$vm_tmpl"

(opt) Transfer the template to the compute node::

   ANSIBLE_TARGETS="$cn,$controller" bin/ansible-playbook \
    ansible/plays/cloud/sync_container.yml -e "lxc_host=$cn lxc_orig_host=$controller lxc_container_name=$vm_tmpl"

Initialise and finish the container provisioning (from scratch)::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=$vm"

Initialise and finish the container provisioning (from template)::

  ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
    ansible/plays/cloud/create_container.yml -e "lxc_container_name=$vm from_container=$vm_tmpl"


