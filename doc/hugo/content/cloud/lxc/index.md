---
title: LXC containers management
tags: [cloud, lxc]
menu:
  main:
    parent: cloud
    identifier: cloud_lxc
    Name: LXC
---

- makinastates lxc container integration consists in:
    - spawning lxc containers including static ip allocation and port mapping
    - providing NAT, DHCP & DNS (dnsmasq & makinastates magicbridge)
    - configuring reverse proxies on the baremetal using:
        - a frontal haproxy proxy incoming https(s) requests
        - iptable to reverse proxy ssh requests

- WARNING currently only those backing store are supported/tested: `dir`, `overlayfs`.

- We name:

    ``$controller``
        : the station from where we will operate to controll other resources

    ``$cn``
        : the compute node where we will spawn LXC containers

    ``$vm``
        : the LXC container to spawn

    ``$vm_tmpl``
        : the name of the container to clone from

## Preliminary configuration

- Go into makina-states folder:

    ```sh
    cd /srv/makina-states
    ```

- Edit [database.sls](/reference/databasesls/), specially ``ips``, ``vms``, & ``cloud_vm_attrs``:

    ```sh
    $EDITOR etc/makina-states/database.sls
    ```

    - ``ips`` should container the ips for ``$controller (usually localhost)``, and the ``$cn``

        ```yaml
        ips:
            mycontainer.foo.loc: 1.2.3.4
        ```

    - ``vms`` should contain a reference to indicate where we will spawn your container

        ```yaml
        vms:
          lxc:
            mycontainer.foo.loc:  # <- baremetal
              - foocontainer.truc.foo # <- container
        ```

    - ``cloud_vm_attrs`` should certainly contain domains to proxy http requests to underlyiung containers

        ```yaml
        cloud_vm_attrs:
          foocontainer.truc.foo:
            domains:
              superapp.truc.foo
        ```

- Define shell variable to copy/paste following commands:

    ```sh
    export controller="$(hostname -f)"
    export cn="$(hostname -f)"
    # export cn="c.foo.net"
    export vm="d.foo.net"
    export vm_tmpl="makinastates"
    ```

## Preparation on the controller
- Refresh cache:

    ```sh
    # bin/salt-call -lall \
    #  state.sls makina-states.services.cache.memcached # the first time
    service memcached restart
    _scripts/refresh_makinastates_pillar.sh
    # or with limit on hosts that the run will be
    ANSIBLE_TARGETS="$controller,$vm,$cn" _scripts/refresh_makinastates_pillar.sh
    ```

## Preinstalling makina-states (controller & each compute node)
- Installing it on controller:

    ```sh
    ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
      ansible/plays/makinastates/install.yml
    ```
- Installing it on compute nodes:

    ```sh
    ANSIBLE_TARGETS="$cn" bin/ansible-playbook \
      ansible/plays/makinastates/install.yml
    ```

## Configure the dns on a full makina-states infra with mc\_pillar

```sh
ANSIBLE_TARGETS="$DNS_MASTER" bin/ansible-playbook \
  ansible/plays/cloud/controller.yml
```

## Compute node related part
- Configure compute\_node with:

```sh
ANSIBLE_TARGETS="$cn" ansible-playbook \
  ansible/plays/cloud/compute_node.yml
```

## Cooking and delivery of container / container templates
- Initialise a lxc container that will be the base of our image (after
creation go edit in it until sastified of the result):

    ```sh
    ANSIBLE_TARGETS="$controller,lxc$vm_tmpl" bin/ansible-playbook \
      ansible/plays/cloud/create_container.yml
    ```
- Synchronise it to an offline image, this will copy the container to the
image, and remove parts from it (like sshkeys) to impersonate it:

    ```sh
    ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
      ansible/plays/cloud/snapshot_container.yml -e "lxc_template=$vm_tmpl lxc_container_name=lxc$vm_tmpl"
    ```
    - Arguments:

        `ANSIBLE_TARGETS`
            : compute node where the container resides (must be in
              ansible inventory)

        `lxc_template`
            : lxc image to create

        `lxc_container_name`
            : lxc container which serve as a base for the image

- Transfer the template to the compute node where you want to spawn
  containers from that image:

    ```sh
    ANSIBLE_TARGETS="$cn" ansible-playbook \
     ansible/plays/cloud/sync_container.yml \
         -e "lxc_orig_host=$controller lxc_container_name=$vm_tmpl"
    ```

    - Arguments:

        `ANSIBLE_TARGETS`
            : both orig and dest

        `lxc_host`
            : where to transfer container/template

        `lxc_orig_host`
            : where from transfer container/template

        `lxc_container_name`
            : lxc container to transfer



## lxc template creation
```sh
release=vivid  # choose your distrib here
lxc-create -t ubuntu -n ${release}
lxc-clone -n lxcmakinastates${release} -o ${release} -- -r ${release}
lxc-attach -n lxcmakinastates${release}
apt-get install git python ca-certificates
git clone https://github.com/makinacorpus/makina-states.git /srv/makina-states
/srv/makina-states/_scripts/boot-salt.sh -C -n lxccontainer --highstates || ( \
    && \
    . /srv/makina-states/venv/bin/activate &&\
    pip install --upgrade pip &&\
    deactivate &&\
    /srv/makina-states/_scripts/boot-salt.sh -C --highstates)
# any additionnal stuff to complete the image
# cmd1
```


## Initialise a container
- Initialise and finish the container provisioning (from scratch)

    ```sh
    ANSIBLE_TARGETS="$cn,$vm" bin/ansible-playbook \
      ansible/plays/cloud/create_container.yml
    ```

    - Arguments:

        `ANSIBLE_TARGETS`
            : compute node where the container resides (must be in ansible inventary) & lxc container to create

        `lxc_from_container`
            : lxc container from which initing the container

        `lxc_backing_store`
            : (opt) backing store to use

- Initialise and finish the container provisioning (from template):

    ```sh
    ANSIBLE_TARGETS="$cn,vm" bin/ansible-playbook \
      ansible/plays/cloud/create_container.yml -e "lxc_from_container=$vm_tmpl"
    ```

- Special case: use overlayfs to create the container:

    ```sh
    ANSIBLE_TARGETS="$cn,$vm" bin/ansible-playbook \
     ansible/plays/cloud/create_container.yml \
      -e "lxc_from_container=$vm_tmpl lxc_backing_store=overlayfs"
    ```

