
.. _build_docker:

Docker
=======

Intro
-------
- Although we are all on the container & microservices front,
  the final goal of the makina corpus team is to have our images using
  **systemd** as the base command.
- Indeed, nowadays, systemd is an extremly if not the most powerful linux too
  l to manage all the lifecycle of processes and the ditch that they can leave
  behind on the behalf of the underlying packagers work. So why, afterall
  preventing us from using all the packaging by running only one process ?
  We are on an **UNIX Like OS** guys...
- In other words, There all the reasons to eat the **microservice pattern**, but
  there is also no reason to eat the **1 process for all soup**.
- We refuse here to hack some stuff around an alternative process manager,
  we want to use the underlying distro as it was packaged.

- makina-states is sufficiently flexible to run in all kind of modes, including
  a docker container, running **systemd** or **not**, **with** or **WITHOUT**
  ``makina-states``.
  This docker can run in unprevileged mode,
  but at the condition of bind-mounting /sys/fs/cgroup. Be sure to have the most
  recent version of systemd under ubuntu-vivid, or **journald** wont start.

- On the host You will also need a special apparmor profile,
  which is provided by makina-states, see ``localsettings/apparmor.sls`` for details.

- The build system is inspired from our more than 20 years or UNIX experience, from
  gentoo to Docker land. One of the goals was to make the 4 core build steps
  in bash and utterly flexibles and easy to override.


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


Layout
++++++
What is good to remember is that it is just a collection of shell scripts, and
to modulate an image building, we provide environ variables and volumes from
a well known data directory, which we expose to the build containers.
Users have just to appropriate the **stageN.sh** scripts and the file layout
to get their projects into a contineous deployment pipeline::

 makina-states/     <- checkout of makina-states
 |- docker/
 |  |- stage0.sh stage1.sh stage2.sh stage3.sh [...] <- default build scripts
 |- data/
    |- globalimage.xxx.yyy.xz <- The OS base tarball (like a lxc container
    |                                                 export)
    |- image1/ (manual image)
    |  |
    |  |- injected_volumes/    <- All what is beneath this level
    |      |- /srv/projects/foobar    will be commited as-is to the image1 image
    |      |- /bootstrap_scripts/
    |          |- Dockerfile.stage0
    |          |- stage0.sh        <- build scripts used for image1
    |          |- stage1.sh           they are always overriden by latest
    |          |- stage2.sh           version of either corpus projects
    |          |- stage3.sh           or default ones (makina-states/docker)
    |
    |
    |- image2/ (image based on a git clone of a corpus based project)
       |
       |- myapp.{js, php, py} -> various code sources files, your project
       |
       |- .git <- as there is also a .salt folder, this signals that this image
       |          wants to build a corpus based project and will deploy the current
       |          changeset inside the image
       |
       |- injected_volumes/    <- All what is beneath this level
       |   |- /srv/projects/foobar    will be commited as-is to the image1 image
       |   |- /bootstrap_scripts/
       |
       |- .salt/
               |- Dockerfile.stage0
               |- stage0.sh        <- will override everything that is in
               |- stage1.sh           injected_volumes/bootstrap_scripts/
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
  This is **Stage0**. we expose here:

    - All the docker related environment (socket, cache, layers)
    - The top of the data dir inside **/docker/data**
    - The image dir
      inside **/injected_volumes**
      and also in **/docker/injected_volumes** (to make them available during
      stage1 build)

- The **Stage1** step involves

    - Launching a container on the behalf of any supported environment variables
      and/or command line arguments.
    - If **MB_BASE** is **scratch**, the build will create from an lxc template
      and using `scratch image`_ as a base a **baseimage-xxx-yyy.tar.gz** tarball
      (or reuse if existing). This is the **OS base image**.
    - This file **baseimage-xxx-yyy.tar.gz** is store on the top of
      the **MS_DATA_DIR** directory.
    - From this image, we launch a new container, ensuring that all
      relevant environment variables and volumes are re-exposed to this
      **stage2** container.
    - Inside the container, we now enter **Stage2** step and run the
      **stage2.sh** script as this container boot command which does:

        - Copy all the content of **/docker/injected_volumes** to **/** ensuring
          the conservation of any **POSIX ACL**. This will of course
          be commited as of your final image.
        - We are not using the **ADD** Dockerfile instruction for
           stage1 because it does not conserve **POSIX ACLS**.
           Those acls are heavily used in makina-states setups.
        - Spawn an init as in **PID=1** (currently: **systemd**)
        - Launch makina-states installation and refresh unless users
          enable it via the **MS_MAKINASTATES_BUILD_FORCE** envionment
          variable (set it to no empty string)
        - Execute **/docker/injected_volumes/bootstrap_scripts/stage3.sh**
          and so enter what we call **stage3**  which by default:

            - (RE)Install any corpus based project
            - May execute a basic test suite to test (only the build) that
              everything is in place, but basically the **stage3** script
              is in control from the user and the stage file that has
              the more chance to be edited by users.

        - Save the **POSIX acls** back to **/acls.txt**
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
 - have to override **DATADIR/<image>/injected_volumes/bootstrap_scripts/stage3.sh**
   to construct an image. The more convenient way is to drop a file at this
   place::

     DATADIR/<image>/image_rootfs/bootstrap_scripts/stage3.sh

To build an image, you set environment variables, and then run

.. code-block:: bash

    docker/stage.py [ARGS]

The scripts support those environment variables, in **user facing order**:

    MS_IMAGE
        Image tarball (like a base lxc container export)
    MS_BASE
        Stage 1 base image (either `scratch image`_ or a real image.
        If stage1 is **scratch**, you need to provide a **baseimage-$os-$release.tar.xz**
        tarball placed in the "data" volume.
        or the script will fetch for you a basic ubuntu container using
        lxc-utils. For those who dont know, **scratch** is a special
        and empty image in the Docker speaking.
    MS_IMAGE_DIR
        Data volume dir to place image related files like stage scripts & injected data
        (default: $DATA_DIR/$MS_IMAGE)
    MS_COMMAND
        Command to use on the resulting image (**/sbin/init**)
    MS_GIT_BRANCH
        Branch for makina-states (**stable**)
    MS_OS
        OS (eg: ubuntu)
    MS_OS_RELEASE
        OS release (eg: vivid)
    MS_GIT_URL
        Url for `makina-states <https://github.com/makinacorpus/makina-states>`_
    MS_DATA_DIR
        Data volume dir to place the **baseimage-$os-$release.tar.xz** file (default: ./data)
    MS_BASEIMAGE
        Filename of the base image
        (default: **baseimage-$os-$release.tar.xz**)
    MS_STAGE0_TAG
        Tag of the stage0 image, by default it will look like
        **makinacorpus/makina-states-ubuntu-vivid-stage0**
    MS_DOCKERFILE_STAGE0
        Path to a **Stage0** builder Dockerfile,
        default to current makina-states one (**docker/Dockerfile.stage0**)
    MS_DOCKER_ARGS
        Any argument to give to the docker run call to the stage0 builder (None)
    MS_DO_SNAPSHOT
        Cleanup all sensible data before saving image (ssh keys, pillars & so on).
        set to empty string to disable
    MS_DO_ACLS
        Save POSIX Acls before saving image.
        set to empty string to disable
    MS_DO_PASSWORDS_RESET
        reset all defined unix user passwords before commiting the image.
        set to empty string to disable

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

    - **<DATADIR>/<IMAGE_NAME>/image_rootfs/srv/pillar**
    - **<DATADIR>/<IMAGE_NAME>/image_rootfs/srv/mastersalt-pillar**
    - **<DATADIR>/<IMAGE_NAME>/image_rootfs/srv/projects**

Technically:
 - all what is behind **/docker/injected_volumes** is copied, via rsync
   with ACL support to the **root (/)** of the image.
 - Any file or directory inside $IMAGEDIR/image_rootfs will override the same
   file at the same place in the same level **injected_volumes** directory.
   The folders are synced via rsync at build time.

**docker/stage.py** can also take any argument that will be used
in the docker run command. Any environment knob defined via CLI args will
override variable setted via environment variables.

Indeed, it is via this trick that you can influence the build system.

.. code-block:: bash

    export MS_IMAGE="mycompany/myimage"
    docker/stage.py -v $PWD:/docker/data

If you do not want to use an empty base image (for example a prebuilt makina-states
image), you can use **MS_BASE** to indicate your base

.. code-block:: bash

    mkdir data2
    export MS_BASE="mycompany/myimage"
    docker/stage.py -v $PWD/data2:/docker/data2

OR

.. code-block:: bash

    docker/stage.py -e MS_BASE="mycompany/myimage"

.. _scratch image: https://docs.docker.com/articles/baseimages/#creating-a-simple-base-image-using-scratch

Default build volumes
+++++++++++++++++++++
Those volumes are exposed in all container stages:

+--------------------------------+-------------------------------------------------+
|    CONTAINER                   | HOST                                            |
+--------------------------------+-------------------------------------------------+
|   /docker/data                 |  $DATADIR                                       |
+--------------------------------+-------------------------------------------------+
|   /docker/injected_volumes     |  $DATADIR/$IMAGE/injected_volumes               |
+--------------------------------+-------------------------------------------------+
|   /docker/makina-states        |  makina-states/                                 |
+--------------------------------+-------------------------------------------------+


Adding data files to commited image
---------------------------------------
Anything (file, dir, symlink) that is placed in the **/docker/injected_volumes**
image data directory will be commited with the image.
The files are copied before **stage2** execution, thus you have them available at build time in their real place inside the root of the conrainer.

Anything that is beyong the **IMAGE_DIR** is available through a volume
(mountpoint)  in the **/docker/data** path inside **stage2** and onwards.

All you have to do is to place what you want to go in your image in this location::

    $DATADIR(/path/makinastates/data)/<IMAGE>/injected_volumes/<stuff>


For example, you will have to place your **fic.txt** in the "**project2** image in, that will live in /foo::

    /srv/mastersalt/makina-states/data/project2/injected_volumes/foo/fic.txt

The principal application is to inject your project code and it's pillar configuration::

    /srv/mastersalt/makina-states/data/project2/injected_volumes/srv/projects/project2/project/...
    /srv/mastersalt/makina-states/data/project2/injected_volumes/srv/projects/project2/pillar/init.sls

Overriding stage scripts, the low level and manual way
------------------------------------------------------
Anything that is placed in the **image_rootfs** image data directory will override
contents which are placedt first in the **/docker/injected_volumes** directory.

The reasoning of this is to provide a simple mean to give custom stage scripts
while most users can still use default script files, and we still use the
last version of those script on a rolling release fashion.

For example, if you want to override for example the **stage3** script,
all you have to do is to place a script in the datadir, in this location::

    DATADIR/<IMAGE>/image_rootfs/bootstrap_scripts/<stage>

For example, you will have to place your **stage3.sh** brewed copy override the **stage3** in the **project2** image in::

Eg, for example, to customize stage3, you will have to place your **stage3.sh**
versions which overrides the default one like this::

    cp /srv/mastersalt/makina-states/docker/stage3.sh /srv/mastersalt/makina-states/data/mycy/p2/image_rootfs/bootstrap_scripts/stage3.sh
    $ED /srv/mastersalt/makina-states/data/mycy/p2/image_rootfs/bootstrap_scripts/stage3.sh

Integration with corpus projects (MAKINA PEOPLE, READ THIS)
------------------------------------------------------------
For corpus based projects based on git, it's even more easier
The idea is that the root of the image is a clone from your git repo,
and is pushed back inside the built image.

This allow you to:

    - Build automatically images based on a corpus project
    - Place **stage** builder files inside your **.salt** directory

Please note that you can only deploy one project per image, which will be called
**app** by convention.

This can of course be only a small orchestration project that orchestrate
building of other project inside the image during the build, but it will
drastically simplify all the files you ll need to place in the injected folder
for the image assembler to grab them later in the build process.

Example:

You just have to clone your image code in the data folder in the data according
to the project repository, and the image name, eg for **mycompany/project3**::

    git clone http://goo/foo.git /srv/mastersalt/makina-states/data/mycompany/myproject3

- Copy and arrange in there all additionnal files like pillars::

    /srv/mastersalt/makina-states/data/srv/projects/app/pillar/init.sls

- For custom stages, you just need to drop them inside your .salt folder.
  For example, to customize the stage3,  you only need to drop a **stage3.sh**
  inside your **.salt** folder alongside your codebase.

- Then build your image::

      MS_IMAGE="mycompany/myproject3" /srv/mastersalt/makina-states/docker/stage.py

Initialise a basic corpus project layout from the stage scripts
----------------------------------------------------------------

To bring bacck everything to everyone, dockerized containers only need
what's needed for the fixperms & install steps::

    mkdir myproject
    docker run --rm -ti  -v $PWD/myproject:/srv/projects/myproject makinacorpus/makina-states-ubuntu-vivid bash
    salt-call --local mc_project.deploy app
    exit

You will have all the neccessary files inside the myproject folder to include them
inside your code repository and hack them to apply your deployment rules.



