---
title: Order of operation
tags: [reference, installation]
weight: 450
menu:
  main:
    identifier: reference_sumup
    parent: reference
---

## Organisation & Workflow
- makina-states primarely use salt to deploy on the targeted environment.<br>
- Our salt states are thought to be used in a special order,<br/>
  and specially when you call salt via the **sls**: [``makina-states.top``](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/top.sls).
    - We apply first the [nodetype](../nodetype) configuration.
    - Then, we will apply the [controllers](../controllers) configuration.<br/>
    - Then, we will apply [localsettings](../localsettings) states
    - After all of the previous steps, we may configure ``services`` like
      sshd, crond, or databases. If we are on the **scratch** mode, no
      services are configured by default.
    - Eventually, we may by able to install projects via ``mc_project``. <br/>
        A project is just a classical code repository which has a ".salt"
      and/or ansible playbooks/roles folder commited with enougth
      information on how to deploy it.

## Registries
- The configuration of any of the formulas (nodetypes, controllers, localsettings,
  services) is handled via Makina-States [registries](../registries).

## History
- Makina-States was first using the salt HighState principle of configuring
  everything.
- was based at fist on ``nodetypes presets`` that were preselected collections of [salt states](https://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html) to apply to the system<br/>
- This is from where the [highstate](https://docs.saltstack.com/en/latest/ref/states/highstate.html) will start to run.
- Recently we cutted off this behavior, and now you must apply them explicitly.<br/>
  Indeed:
    - highstate tend to grow and when you decide to reapply it you may
  accidentaly deliver things you forgotten of.
    - It's long, very long to wait to reapply everything for small changes.

