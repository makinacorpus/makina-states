
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


Construct a base docker image with makina-states
---------------------------------------------------
Abstract
++++++++++
We provide a pipeline of 4 small shell scripts that bootstrap a proper
build environment for systemd containers based on ubuntu from **ground0** to
**mars**.

Those shell script are responsible of executing those containers
and run inside a build procedure, which should in most case also include
a test(selfcheck) procedure. Upon a sucessful build, a candidate image
is taggued.

All what is need for most projects is to create the injected volumes and the
**stage3.sh** script and onwards, other script are somewhat **core** and have
merely no change to have any change needs.

All that the user has to do to initiate a build pipeline is:

 - Setup a docker daemon with makina-states & a proper apparmor profile.
 - clone a copy of the makina-states repository to a location of your choise,
   with of course plenty if space under that root.

All commands must then be executed from the root of the repository.

What is good to remember is that it is just a collection of shell scripts, and
to modulate an image building, we provide environ variables and volumes from
a well known data directory which has this Layout for the user to populate
and/or edit any of the build procedure::

 makina-states/
 |- docker/
 |  |- stage0.sh stage1.sh stage2.sh stage3.sh [...] <- default build scripts
 |- data/
    |- globalimage.xxx.yyy.xz
    |- injected_volumes/
       |
       |- image1/               <- All what is beneath this level
        |- /srv/projects/foobar    will be commited as-is to the image1 image
        |- /bootstrap_scripts/
            |- Dockerfile
            |- stage0.sh        <- build scripts used for image1
            |- stage1.sh           If they are not already present, default ones are used
            |- stage2.sh
            |- stage3.sh


DESIGN: The full order of operation
++++++++++++++++++++++++++++++++++++++
As the makina-states images are based upon a funtionnal init system (systemd)
for operation.

To initiate a build, the user can:

- Maybe place a precompiled base image in in the **DATA DIR**.
- Maybe populate **injected_volumes** in the **DATA DIR** for the particular
  image we are building. Basically,
  all what will be placed in **<DATADIR>/$IMAGE/injected_volumes** will
  be copied as-is and commited to the final image.

Their initial build is a bit tedious in sense that they need at least a **3 steps build**.
Hopefully, we provide a script which has batteries included for you.

The procedure will then almost initially look like:

- Create a container which has the necessary environment to build the images.
  This is **Stage0**.
- The **Stage1** step involves

    - Launching this container modulating the invocation via
      environment variables and/or command line arguments.
      This one of the means that end user may influence how to build the final image
      that will be generated from :

        - the container template
        - the **baseimage.tar.xz** or the providen **MS_BASE**
        - the injected volumes **/injected_volumes**

    - If **MB_BASE** is **scratch**, the build will use
      a `scratch image`_,
      It creates **baseimage-xxx-yyy.tar.gz** or reuse it,
      this is the OS base image.
      By default, we export/read this image to/from the top of
      the **MS_DATA_DIR** directory.
    - From this image, we launch a new container, ensuring that all
      relevant environment variables and volumes are injected
    - Inside the container, we now enter **Stage2** step and run the
      **stage2.sh** script as this container boot command.
      The default **stage2** script does the following

        - We copy all the content of **/injected_volumes** to **/** ensuring
          the conservation of any **POSIX ACL**. This will of course
          be commited as of your final image.

          .. note:

              We are not using the **ADD** Dockerfile instruction for
              stage1 because it does not conserve **POSIX ACLS**.
              Those acls are heavily used in makina-states setups.

        - Spawn an init as in **PID=1** (currently: **systemd**)
        - Launch makina-states installation and refresh
        - Execute **/injected_volumes/bootstrap_scripts/stage3.sh**
          and so enter what we call **stage3**  which by default:

            - (RE)Install any corpus based project
            - May execute a basic test suite to test (only the build) that
              everything is in place.

        - Save the **POSIX acls** to **/acls.txt**
        - Mark the container to restore acls on next boot via touching **/acls.restore**
        - If all the build is sucessfull, commit this container
          as an image taggued with the **candidate** keyword.

How To
++++++++++
The entry point to this build system is **docker/stage.py**.

You can override any of the **docker/stageX.sh** scripts by looking and overriding
them to your needs.
For stages > 0, Don't edit them, but use the environment
variables or docker volumes (as stage0.sh arguments) to use your custom scripts.

In most cases, you certainly only:

 - place files and directories inside **DATADIR/<image>/injected_volumes**
 - have to override **DATADIR/<image>/bootstrap_scripts/stage3.sh**
   to construct an image

.. code-block:: bash

    docker/stage.py [ARGS]

The scripts support those environment variables, in **user facing order**:

    MS_IMAGE
        Image tarball (like a base lxc container export)
    MS_BASE
        Stage 1 base image (either `scratch image`_ or a real image.
        If stage1 is **scratch**, you need to provide a **baseimage.tar.xz**
        tarball placed in the "data" volume.
        or the script will fetch for you a basic ubuntu container using
        lxc-utils. For those who dont know, **scratch** is a special
        and empty image in the Docker speaking.
    MS_DATA_DIR
        Data volume dir to place the **baseimage.tar.xz** file (default: ./data)
    MS_IMAGE_DIR
        Data volume dir to place image related files like stage scripts & injected data
        (default: $DATA_DIR/$MS_IMAGE)
    MS_GIT_BRANCH
        Branch for makina-states (**stable**)
    MS_OS_RELEASE
        OS release (eg: vivid)
    MS_GIT_URL
        Url for `makina-states <https://github.com/makinacorpus/makina-states>`_
    MS_OS
        OS (eg: ubuntu)
    MS_COMMAND
        Command to use on the resulting image (**/sbin/init**)
    MS_BASEIMAGE
        Filename of the base image
        (default: **baseimage-${MS_OS}-${MS_OS_RELEASE}.tar.xz**)
    MS_STAGE0_TAG
        Tag of the stage0 image, by default it will look like
        **makinacorpus/makina-states-ubuntu-vivid-stage0**
    MS_DOCKERFILE
        Path to a **Stage0** builder Dockerfile,
        default to current makina-states one
    MS_DOCKER_ARGS
        Any argument to give to the docker run call to the stage0 builder (None)

Read Only variables:

    MS_STAGE1_NAME
        Name of the stage1 container (use to mount volumes from host in stage2
        and onwards)
    MS_STAGE2_NAME
        Name of the stage2 container  (used to commit the final image)

Additionnaly, in stage1 (read-only):

    MS_IMAGE_CANDIDATE
        Tag of the Image to commit if the build is sucessful,
        default to **$MS_IMAGE:candidate**

You can feed the image with preconfigured pillars & project trees
by creating files inside for example:

    - **<DATADIR>/<IMAGE_NAME>/injected_volumes/srv/pillar**
    - **<DATADIR>/<IMAGE_NAME>/injected_volumes/srv/mastersalt-pillar**
    - **<DATADIR>/<IMAGE_NAME>/injected_volumes/srv/projects**

Those pillars, if given will be fullycommited to the image.
Technically, all what is behind **injected_volumes** is copied, via rsync
with ACL support to the image.

**docker/stage.py** can also take any argument that will be used
in the docker run command. Any environment knob defined via CLI args will
override variable setted via environment variables.

Indeed, it is via this trick that you can influence on the behavior of the
**docker_build_stage2.sh** (**Stage2**) script and **onwards** stages.

.. code-block:: bash

    export MS_IMAGE="mycompany/myimage"
    docker/stage.py \
     -v $PWD:/docker/data \
     -v /path/to/custom/docker_build_stage2.sh:/bootstrap_scripts/docker_build_stage2.sh\
     -v /path/to/custom/docker_build_stage3.sh:/bootstrap_scripts/docker_build_stage3.sh

If you do not want to use an empty base image (for example a prebuilt makina-states
image), you can use **MS_BASE** to indicate your base

.. code-block:: bash

    mkdir data
    export MS_BASE="mycompany/myimage"
    docker/stage.py \
      -v $PWD/data:/docker/data \
      -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh

OR

.. code-block:: bash

    docker/stage.py \
        -e MS_BASE="mycompany/myimage"
        -v $PWD:/docker/data \
        -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh

.. _scratch image: https://docs.docker.com/articles/baseimages/#creating-a-simple-base-image-using-scratch

Adding data files to commited image
---------------------------------------
Anything (file, dir, symlink) that is placed in the **injected_volumes** image data directory will be commited with the image.

The files are copied before **stage2** execution, thus you have them available at build time.

All you have to do is to place what you want to go in your imag in this location::

    DATADIR/<IMAGE>/injected_volumes/<stuff>

For example, you will have to place your **fic.txt** in the "**project2** image in, that will live in /foo::

    /srv/mastersalt/makina-states/data/project2/injected_volumes/foo/fic.txt

The principal application is to inject your project code and it's pillar configuration::

    /srv/mastersalt/makina-states/data/project2/injected_volumes/srv/projects/project2/project/...
    /srv/mastersalt/makina-states/data/project2/injected_volumes/srv/projects/project2/pillar/init.sls

Overriding stage scripts
-----------------------------
Anything that is placed in the **overrides** image data directory will override things which are placed
at first in the **injected_volumes** directory.

The reasoning of this is to provide a simple mean to give custom stage scripts while most user can still use default script files.

For example, if you want to override for example the **stage3** script,
all you have to do is to place a script in the datadir, in this location::

    DATADIR/<IMAGE>/overrides/injected_volumes/bootstrap_scripts/<stage>

For example, you will have to place your **stage3.sh** brewed copy override the **stage3** in the **project2** image in::

    /srv/mastersalt/makina-states/data/project2/overrides/injected_volumes/bootstrap_scripts/stage3.sh

Assuming that your makina-states installation copy is installed in **/srv/mastersalt**.

Subdirectories are supported as well (for subrepos).

Eg, for example, you will have to place your **stage3.sh** brewed copy override the **stage3** in the "**mycy/p2** image in::

    /srv/mastersalt/makina-states/data/mycy/p2/overrides/injected_volumes/bootstrap_scripts/stage3.sh

