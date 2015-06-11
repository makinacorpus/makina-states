
.. _build_docker:

Docker
=======

Intro
-------
- Although we are all on the container & microservices front, the final goal
  of the makina corpus team is to have base images with systemd.
- Nowadays, systemd is an extremly powerful tool to manage all the lifecycle
  of processes and the ditch that they can leave behind on the behalf of
  the underlying packagers work, so why preventing us from using it ?
- In other words, There all the reasons to eat the **microservice pattern**, but
  there is also no reason to eat the **1 process for all soup**.
- We refuse here to hack some stuff around an alternative process manager,
  we want to use the underlying distro as it was packaged.

- makina-states is sufficiently flexible to run in all kind of modes, including
  a docker container, running systemd. This docker can run in unprevileged mode,
  but at the condition of bind-mounting /sys/fs/cgroup. Be sure to have the most
  recent version of systemd under ubuntu-vivid, or **journald** wont start.

- On the host You will also need a special apparmor profile,
  which is provided by makina-states, see ``localsettings/apparmor.sls`` for details.

- The build system is inspired from our more than 20 years or UNIX experience, from
  gentoo to Docker land.

DESIGN: The full order of operation
------------------------------------
As the makina-states images are based upon a funtionnal init system (systemd)
for operation,
Their initial build is a bit tedious in sense that they need a 3 steps build.
Hopefully, we provide a script which has batteries included for you.

The script will:

- Create a container which has the necessary environment to build the images.
  This is **Stage0**.
- The **Stage1** step involves

    - Launching this container and by modifying
      environment variables and/or command line arguments,
      the user may influence how to build the final image that will be
      generated from :

        - the container template
        - the **baseimage.tar.xz** or the providen **MS_BASE**

    - If **MB_BASE** is **scratch**, the build will use
      a `scratch image`_,
      It creates **baseimage.tar.gz** or reuse it,
      this is the OS base image.
      By default, we export this image to the **MS_DATA_DIR** directory.
    - From this image, we launch a new container, ensuring that all
      relevant environment variables and volumes are forwarded
    - Inside the container, what we call **Stage2** does:

        - we execute the **/data/build_docker.sh** script which by default:
        - Maybe copy the inputed pillar, mastersalt pillar &
          corpus pillars inside this container, they are currently mounted as volumes
          in **/forwarded_volumes** by **Stage1**
        - spawn init (currently: systemd)
        - launch makina-states installation
        - We then enter **Stage3** which by default

            - (RE)Install any corpus based project
            - May execute a basic test suite to test (only the build) that
              everything is in place.

        - Save the **POSIX acls** to **/acls.txt**
        - Mark the container to restore acls on next boot via touching **/acls.restore**
        - If all the build is sucessfull We commit this container as an image
          but taggued with the **candidate** keyword.


Construct a base docker image with makina-states
---------------------------------------------------
Idea
++++++++
All that the user has to do, is to copy the **_script/docker_build.sh**
in his project and adapt it for it's need, basically, the only thing
to change in a corpus based project is the test procedure.

What you, as a regular user, will want to change is likely to be only
a part of **Stage3** or (future) upper stages.

How To
++++++++++
The entry point to this build system is **_scripts/build.sh**
You can easily adjust it to your needs in case.

.. code-block:: bash

    _scripts/build.sh

You can override **docker_build.sh** (installing makina-states) by looking and overriding
it to your need

The script support those environment variables:

    MS_DOCKERFILE
        Path to a Stage0 Compliant file,
        default to current makina-states one
    MS_DATA_DIR
        Data volume dir to place the **baseimage.tar.xz** file
    MS_DOCKER_ARGS
        Any argument to give to the docker run call to the stage0 builder (None)
    MS_BASE
        Stage 1 base image (either `scratch image`_ or a real image.
        If stage1 is scratch_ , you need to provide a **baseimage.tar.xz**
        tarball placed in the "data" volume.
        or the script will fetch for you a basic ubuntu container using
        lxc-utils. For those who dont know, **scratch** is a special
        and emppty image in the Docker speaking.
    MS_COMMAND
        Command to use on the resulting image
    MS_GIT_BRANCH
        Branch for makina-states (stable)
    MS_GIT_URL
        Url for `makina-states <https://github.com/makinacorpus/makina-states>`_
    MS_OS
        OS (eg: ubuntu)
    MS_OS_RELEASE
        OS release (eg: vivid)
    MS_IMAGE
        Image tarball (like a base lxc container export)
    MS_STAGE0_TAG
        Tag of the stage0 image, by default it looks like
        **makinacorpus/makina-states-vivid-0**
    MS_DOCKER_STAGE1
        Path to a **stage1** builder script, eg **`_scripts/docker_build_stage1.sh <https://github.com/makinacorpus/makina-states/blob/master/_scripts/docker_build_stage1.sh>`_**
    MS_DOCKER_STAGE2
        Path to a **stage2** builder script, eg **`_scripts/docker_build_stage2.sh <https://github.com/makinacorpus/makina-states/blob/master/_scripts/docker_build_stage2.sh>`_**
    MS_DOCKER_STAGE3
        Path to a **stage2** builder script, eg **`_scripts/docker_build_stage3.sh <https://github.com/makinacorpus/makina-states/blob/master/_scripts/docker_build_stage3.sh>`_**

Additionnaly, in stage2, the stage0 script will set:

    MS_IMAGE_CANDIDATE
        Which is the tag of the Image to commit if the build is sucessful

You can feed the image with preconfigured pillars & project trees
by mounting additional volumes for:

    - **/srv/pillar**
    - **/srv/mastersalt-pillar**
    - **/srv/projects**

Those pillars, if given will be commited to the image.

**_scripts/build.sh** can also take any argument that will be used
in the docker run command. Any environment knob defined via CLI args will
override variable setted via environment variables.

Indeed, it is via this trick that you can influence on the behavior of the
**docker_build_stage2.sh** (**Stage2**) script and **onwards** stages.

.. code-block:: bash

    export MS_IMAGE="mycompany/myimage"
    _scripts/build.sh \
     -v $PWD:/data \
     -v /path/to/custom/docker_build_stage2.sh:/bootstrap_scripts/docker_build_stage2.sh\
     -v /path/to/custom/docker_build_stage3.sh:/bootstrap_scripts/docker_build_stage3.sh

If you do not want to use an empty base image (for example a prebuilt makina-states
image), you can use **MS_BASE** to indicate your base

.. code-block:: bash

    export MS_BASE="mycompany/myimage"
    _scripts/build.sh \
      -v $PWD:/data \
      -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh

OR

.. code-block:: bash

    _scripts/build.sh \
        -e MS_BASE="mycompany/myimage"
        -v $PWD:/data \
        -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh

.. _scratch image: https://docs.docker.com/articles/baseimages/#creating-a-simple-base-image-using-scratch

