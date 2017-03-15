Makina-States based docker Images
=====================================

.. contents::

Rules
-----
- Docker images share a common layout, and inherit from the ``makina-states`` base images from docker-hub.
- Applications are deployed into those containers via :ref:`mc_project <project_creation>`.
- Those images use **mc_project** in ``remote_less`` mode and should not rely on a full
  system running, we are in a docker. For long living processes, use circus.
- Runtime include an ``initial pre-re-configure step`` before launching the app
  and the entry point lives into ``$project_root/bin/launch.sh``

    - Ideally, there is a ``mc_launcher.py`` saltstack module to orchestrate the whole reconfigure step.

- Images include at least 2 mountpoints for the ``logs`` and the ``data`` folders.

Run time
++++++++++
The app is launched an managed via a ``bin/launch.sh`` (`Example <https://github.com/makinacorpus/corpus-dockerregistry/blob/master/bin/launch.sh>`_) script, which should ideally:

  - Replace the default pillar by the **configuration/pillar.sls** if it
    existsa. This is the only thing we need to do before launching a salt
    module script that does the rest.
  - Execute a salt **mc_launcher.py** (`Example <https://github.com/makinacorpus/corpus-dockerregistry/blob/master/.salt/_modules/mc_launcher.py>`_) module which runs our app after maybe
    having reconfigured it.

      - allow inbound ssh connections for allowed keys
      - reconfigure (ideally by exec'ing a subset of the sls in **.salt**)
        the container to serve the app (eg: update domain to server,
        ip of the database, registration to autodiscovery service)
      - spawn a circus daemon at the end of the configuration.
      - The module should have at least implements this interface:

        .. code-block:: python

            def sshconfig(name=PROJECT):
                '''code to allow ssh_keys to connect'''
                pass
            def reconfigure(name=PROJECT):
                '''code to reconfigure the app to serve requests
                  in this specific context'''
                pass
            def launch(name=PROJECT, ssh_config=False, re_configure=False):
                if ssh_config:
                    ssh_config(name=name)
                if re_configure
                    re_configure(name=name)
                # code to launch the app in foreground

- Indeed, the app is lightly reconfigured via salt and may be given an
  overriden pillar file via a filesystem volume to help to reconfigure it.
  **Think to rename the pillar configuration key along with the name of your project**
  See :ref:`mc_project configuration pillar file <mc_project_pillar>`
- Volumes and files that need to be prepolulated should be filled by the
  launcher if and only if it is not already data placed into them.
- A Control-C or quit signal must inhibit any launched process more or less
  gracefully

Build time
++++++++++++++++
- We configure the image through a regular :ref:`mc_project <project_creation>` based
  saltstack project.
- All the processes inside the container must be managed if possible via circus
- POSIX Acls are now to be avoided at all cost to avoid export/import problems as tar
  is used to exchange images, the extended attributes are lost in the middle


layout inside the Image
-------------------------
This is of course an example but it reflects what we need to respect::

    /srv/salt/custom.sls      <- custom pillar
    /srv/projects/<project>
       |
       |- project/ <- application code
       |     |- Dockerfile    <- Each app needs to have a basic Dockerfile
       |     |- bin/launch.sh <- launcher that:
       |     |                   - copy $data/configuration/pillar.sls -> $pillar/init.sls
       |     |                   - reconfigure (via salt) the app
       |     |                   - launch the app in foreground
       |     |- .salt         <- deployment and reconfigure code (mc_project based)
       |     |- .salt/100_dirs_and_prerequisites.sls
       |     |- .salt/200_reconfigure.sls
       |     |- .salt/300_nginx.sls
       |     |- .salt/400_circus.sls
       |     |- .salt/_modules/mc_launcher.py
       |                code that is used to reconfigure the image
       |                at launch time (via launch.sh)
       |
       |- pillar/  <- salt extra pillar that overrides PILLAR.sample (itself
       |              overriden by data/configuration/pillar.sls)
       |
       |- data/                  <- exposed through a docker volume
             |- data/            <- persistent data root
             |- configuration/   <- deploy time pillar that is used at reconfigure
                                     time (startup of a pre-built image)


Initialise your dev environment
----------------------------------------
We separate the project codebase from any persistent data that is needed to be created along any container.
Those folders will be mounted inside the running container as docker volumes.

    - one dedicated for the clone of the codebase: **${PROJECT}**
    - one dedicated for the persistent data & configuration: **${DATA}**
    - a subdirectory of data is exposed as a docker volume: **${VOLUME}**

If you run a prebuilt image, you may not need the project codebase folder.

By convention, the name of the persistant data holding directory is the name of the clone folder suffixed by ``_data``.
Eg if you clone your project inside ``~/project``, the data folder will be ``~/project_data``.
The data folder can't and must not be inside the project folder as we drastically play with
unix permissions to enforce proper security and the two of those folders do not have at all the same policies.
The special folder **project_data/volume** is mounted as a docker voume inside the container at the project data directory location. We refer it as **${VOLUME}**.

You need to add a volume that will contains those subdirs:

    ${PROJECT}/
        git clone of this repository, the project code inside the
        container. this folder contains a '.salt' folder which
        describe how to install & configure this project.
        (/srv/projects/<name>/project)
    ${PROJECT}/Dockerfile
        Dockerfile to build your app
    ${PROJECT}/.salt
        mc_project configuration to configure your app
    ${DATA}/volume/ aka **${VOLUME}**
        mounted as the persistent data folder inside the container
        (/srv/projects/<name>/data)
    ${DATA}/volume/configuration
        directory holding configuration bits for the running container
        that need to be edited or accessible from the host & the user
    ${DATA}/volume/data
        persistent data

Inside of the data volume, we also differentiate in term of permissions
the configuration from the datas (later is more laxist).
For the configuration directories, after the image has been launched, you ll
certainly need to gain root privileges to re-edit any files in those subdirs.

Project_data in details:

    ${VOLUME}/ssh/\*.pub
        ssh public keys to allow to connect as root
    ${VOLUME}/configuration
        contains the configuration
    ${VOLUME}/configuration/pillar.sls
        configuration file (saltstack pillar) for the container
    ${VOLUME}/data/
        top data dir

Download and initialize the layout
+++++++++++++++++++++++++++++++++++

.. code-block:: bash

    export REPO_URL="http://git/orga/repo.git"
    export PROJECT="${WORKSPACE}/myproject" # where you want to put the code
    export DATA="${PROJECT}_data"           # where you want to put the data
    export VOLUME="${DATA}/volume"          # where you want to put the docker volume
    mkdir -p "${DATA}" "${VOLUME}"
    git clone "${REPO_URL}" "${PROJECT}"

OPTIONNAL: Generate a a certificate with a custom authority for testing purposes
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This script will generate a CA and sign a wildcard certificate for CN="${DOMAIN}" with it
.. code-block:: bash

    gen_password() { < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-64};echo; }
    DATA="${DATA:-$(pwd)}"
    CA_PATH="${CA_PATH:-${DATA}/ca}"
    C="${C:-FR}"
    L="${L:-Paris}"
    ST="${ST:-IleDeFrance}"
    CA="${CA:-"dockerca"}"
    EXPIRY="${EXPIRY:-$((365*100))}"
    DOMAIN="${DOMAIN:-"registryh.docker.tld"}"
    mkdir -p "${CA_PATH}"
    cd "${CA_PATH}"
    CA_PASSWD="$(cat ca_passwd 2>/dev/null)"
    DOMAIN_PASSWD="$(cat "${DOMAIN}_passwd" 2>/dev/null)"
    CA_PASSWD="${CA_PASSWD:-$(gen_password)}"
    DOMAIN_PASSWD="${DOMAIN_PASSWD:-$(gen_password)}"
    echo "$CA_PASSWD" > ca_passwd
    echo "$DOMAIN_PASSWD" > "${DOMAIN}_passwd"
    if ! test -e ca_key.pem;then
        openssl genrsa -des3 -passout file:ca_passwd -out sca_key.pem
        openssl rsa -in sca_key.pem -passin file:ca_passwd -out ca_key.pem
    fi
    if ! test -e ca.crt;then
        openssl req -new -x509 -days ${EXPIRY} -key ca_key.pem -out ca.crt\
          -subj "/C=${C}/ST=${ST}/L=${L}/O=${CA}/CN=${CA}/"
    fi
    if ! test -e "${DOMAIN}_key.pem";then
        openssl genrsa -des3 -passout "file:${DOMAIN}_passwd" -out "s${DOMAIN}_key.pem"
        openssl rsa -in "s${DOMAIN}_key.pem" -passin "file:${DOMAIN}_passwd" -out "${DOMAIN}_key.pem"
    fi
    if ! test -e "${DOMAIN}.crt";then
        openssl req -new -key "${DOMAIN}_key.pem" -out "${DOMAIN}.csr"\
          -subj "/C=${C}/ST=${ST}/L=${L}/O=${CA}/CN=*.${DOMAIN}/"
        openssl x509 -CAcreateserial -req -days ${EXPIRY} -in ${DOMAIN}.csr\
          -CA ca.crt -CAkey ca_key.pem -out "${DOMAIN}.crt"
    fi
    cat "${DOMAIN}.crt" "ca.crt"                     > "${DOMAIN}.bundle.crt"
    cat "${DOMAIN}.crt" "ca.crt" "${DOMAIN}_key.pem" > "${DOMAIN}.full.crt"
    chmod 644 *crt*
    chmod 640 *key* *full.crt *_passwd


Register the certificate to the host openssl configuration
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
.. code-block:: bash

    cat | sudo sh << EOF
    cp "${DATA}/ca/${domain}.bundle.crt /usr/local/share/ca-certificates\
    && update-ca-certificates
    EOF

Configure the image via the salt PILLAR
+++++++++++++++++++++++++++++++++++++++++++
You need then to fill the pillar to reconfigure your container at running time.
  - setup a domain to serve for the registry (the virtualhost name)
  - (opt) the SSL certificate informations

.. code-block:: bash

    mkdir -p "${VOLUME}/configuration"
    cp .salt/PILLAR.sample "${VOLUME}/configuration/pillar.sls"
    sed -re "s/makina-projects.projectname/makina-projects.registry/g"\
      -i "${VOLUME}/configuration/pillar.sls"
    $EDITOR "${VOLUME}/configuration/pillar.sls" # Adapt to your needs

Build & Run
---------------
**Be sure to have completed the initial configuration (SSL, PILLAR) before launching the container.**
You may not need to **build** the image, you can directly download it from the docker-hub.

.. code-block:: bash

    docker pull <orga>/<image>
    # or docker build -t <orga>/<image> .

Run

.. code-block:: bash

    docker run -ti -v "${VOLUME}":/srv/projects/<project>/data <orga>/<image>

DNS configuration
++++++++++++++++++
When your container is running and you want to access it locally, in development mode,<br/>
just inspect and register it in your /etc/hosts file can avoid you tedious setup

Assuming that you configured the container to respond to **${DOMAIN}**.

.. code-block:: bash

    IP=$(sudo docker inspect -f '{{ .NetworkSettings.IPAddress }}' <YOUR_CONTAINER_ID>)
    cat | sudo sh << EOF
    sed -i -re "/${DOMAIN}/d" /etc/hosts
    echo $IP ${DOMAIN}>>/etc/hosts
    EOF

List of example images
---------------------------
- `docker registry <https://github.com/makinacorpus/corpus-dockerregistry>`_



