---
title: Usage
tags: [topics, installation]
---

## Switch makina-states branch
- To switch on a makina-states branch, like the **v3** branch in
  production:

    ```sh
    bin/boot-salt2.sh -b v3
    ```

## Update makina-states local copy
- To sync makinastates code

    ```sh
    bin/boot-salt2.sh -C -S
    ```

## Running makinastates in highstate mode
- To install all enabled makina-states services after having configured
  your pillar up

    ```sh
    bin/boot-salt2.sh -n laptop|server|lxccontainer|vm -C && \
        bin/salt-call --retcode-passthrough state.sls makina-states.top
    ```

## Upgrade
- Upgrade will:
    - Run predefined & scheduled upgrade code
    - Update makina-states repositories in /srv/salt & /srv/makina-states
    - Update core repositories (like salt code source in /srv/makina-states/src/salt)
    - Do the highstates (salt and masterone if any)

    ```sh
    bin/boot-salt2.sh -C --S  && \
        bin/salt-call --retcode-passthrough state.sls makina-states.top
    ```
## use ansible & salt
- [Salt](salt)
- [Ansible](ansible)
