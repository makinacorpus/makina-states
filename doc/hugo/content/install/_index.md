---
title: Installation
tags: [installation, install, upgrade]
weight: 100
---

**REMEMBER THAT FOR NOW YOU HAVE TO USE UBUNTU &gt;= 14.04.**

**Use root unless you understand well how it works to handle user install**

### Download
- Get MakinaStates by cloning it from github<br/>
  Usually we install it in ``/srv/makina-states``

    ```sh
    git clone http://raw.github.com/makinacorpus/makina-states /srv/makina-states
    ```
## Common install command
- Install with ``scratch`` node, with refresh cron, logrotate.

    ```sh
    bin,/boot-salt2.sh -C --install-logrotate --install-crons
    ```

### boot-salt2.sh, the makina-states installer & manager
- ``boot-salt2.sh`` will try to remember how you configured makina-states on
  each run. It stores configs in ``<clone_dir>/etc/makina-states``

- You can see the help this way:

    ```sh
    bin/boot-salt2.sh --help  # Short overview:
    bin/boot-salt2.sh --long-help  # Detailed overview:
    ```

- If you want to install  with default options (scratch)<br/>

    ```sh
    bin/boot-salt2.sh -C
    ```

## Optional post install steps

- Install the logrotate to rotate salt logs
    ```sh
    bin/boot-salt2.sh -C --install-logrotate
    ```

- Install the cron that refresh makina-states code every since and then (15min)
    ```sh
    bin/boot-salt2.sh -C --install-crons
    ```

- Install the salt & ansible binaries to /usr/local/bin.<br/>
  **THIS IS NOT RECOMMENDED ANYMORE, AND EVEN HARMFULL**
    ```sh
    bin/boot-salt2.sh -C --install-links
    ```

## Related documents
- [Usage](../usage)
- [Layout](../reference/layout)
- [database.sls](../reference/databasesls)
- [nodetypes](../reference/nodetypes)

