Create lxc containers in a cloud
===================================
workflow:

Edit database::

  vim etc/makina-states/database.sls

Define shell variable to copy/paste following commands::

    export ms_controller="a.foo.net"
    export ms_cn="c.foo.net"
    export ms_vm="d.foo.net"

Refresh cache::

  service memcached restart
  _scripts/refresh_makinastates_pillar.sh

Install controller/dns with::

  ansible-playbook ansible/plays/cloud/controller.yml \
    -e "makinastates_controller=$ms_controller"

Preinstall makina-states on compute_node with::

  ansible-playbook ansible/plays/makinastates/install.yml -e "hosts=$ms_cn"

Or on a makina-states v1 node, unwire old ms and install msv2::

  ansible-playbook ansible/plays/makinastates/migv2.yml -e "hosts=$ms_cn"

Configure compute_node with::

  ansible-playbook ansible/plays/cloud/controller.yml \
    -e "makinastates_compute_node=$ms_cn"

(opt) Prepare a lxc container image and snapshot with with::

(opt) Synchronnise it to an offline image::

(opt) Transfer the template to the compute node::

Initialise and finish the container provisioning::

