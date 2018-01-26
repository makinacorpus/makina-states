---
title: Salt
tags: [usage, salt]
weight: 300
menu:
  main:
    parent: usage
    identifier: usage_salt
---

## Command log level
Remember that ``-lall`` refers to the loglevel **all**.<br/>
You can lower the output level by lowering down to **info** (``-linfo``).

## Run a salt state
```sh
    bin/salt-call -lall --retcode-passthrough state.sls <STATE>
```


## Run a salt function

```sh
    bin/salt-call -lall --retcode-passthrough test.ping
```


## Configure a pillar entry
- **pillar/pillar.d/myentry.sls**

```text
---
makina-states.foo.bar: bal

```
