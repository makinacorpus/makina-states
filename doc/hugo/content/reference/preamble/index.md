---
title: Preamble
tags: [topics, installation]
menu:
    main:
        parent: reference
        identifier: reference_preamble
weight: 0
---

## Briefing
- MakinaStates at a whole is a combination of [ansible](https://www.ansible.com/) and [salt](https://docs.saltstack.com/en/latest/) aiming at operating a cluster from baremetal to projects
  delivery.

- Note that makina-states <b>do not use regular salt daemons(minion/master) to operate remotely <br/>
 but an ansible bridge that copy the pillar and use salt-call locally
 directly on the remote box via SSH</b>
- Ansible get the information from makinastates by getting the salt pillar
  for a particular through a custom dynamic inventory.

## Compatibility
- For now, you will have to use <b>Ubuntu &gt;= 14.04</b>.<br/>
  Makina-States can be ported to any
  linux based OS, but we, here, use ubuntu server and this is the only
  supported system for now. <br/>
  It can be used in any flavor: lxc, docker, baremetal, kvm, etc.
