
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

Construct a base docker image with makina-states
---------------------------------------------------
As the makina-states images are based upon systemd for operation,
their initial build is a bit tedious in sense that they need a 3 steps build.

STAGE 1: construct the image builder
+++++++++++++++++++++++++++++++++++++

The goal of this step is to make a base chroot proper to the makina-states initialization::

    git clone https://github.com/makinacorpus/makina-states.git -b stable
    cd makina-states
    docker build -t makina-states-vivid-0 -f Dockerfile.vivid.stage0  .

STAGE 5 (2+3): build images (base+app)
+++++++++++++++++++++++++++++++++++++++
::

    docker run --privileged -ti --rm \
        -e MS_BASE="scratch" -e MS_IMAGE="makinacorpus/makina-states-vivid"\
        -v /usr/bin/docker:/usr/bin/docker:ro \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /var/run/docker:/var/run/docker \
        -v /var/lib/docker:/var/lib/docker \
        -v /sys/fs:/sys/fs:ro\
        -v $PWD:/data \
        -v $PWD/_scripts/docker_build.sh:/bootstrap_scripts/docker_build.sh \
        makinacorpus/makina-states-vivid-0

You can override docker_build (installing makina-states) by looking and overriding
the **_scripts/docker_build.sh** script. The previous command will be::

    docker run --privileged -ti --rm \
        -e MS_BASE="scratch" -e MS_IMAGE="makinacorpus/makina-states-vivid"\
        -v /usr/bin/docker:/usr/bin/docker:ro \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /var/run/docker:/var/run/docker \
        -v /var/lib/docker:/var/lib/docker \
        -v /sys/fs:/sys/fs:ro\
        -v $PWD:/data \
        -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh\
        makinacorpus/makina-states-vivid-0

You can feed the image with preconfigured pillars by mounting additional volumes for:

    - **/srv/pillar**
    - **/srv/mastersalt-pillar**
    - **/srv/projects/<project>/pillar/**

This will generate a **baseimage.baseimage.tar.xz** in the current directory.
This will also generate 2 images:

    - one for the base image containing a bare ubuntu lxc container.
      If we find the data avolume the base image, we won't reconstruct it.
      If we find the image inside the local docker image registry, we won't reconstruct it
    - one containing makina-states (provisionned via mastersalt + salt + projects dance)

Basically, it is just an export of a basic ubuntu LXC container created via the lxc utils.

STAGE 2
++++++++
You can then eventually build the base image via
```
docker build -t makinacorpus/makina-states-vivid-0 -f Dockerfile.vivid
DID=$(docker run --cap-add=SYS_ADMIN  -d makinacorpus/makina-states-vivid-0)
```

