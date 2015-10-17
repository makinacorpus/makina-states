Makina-States based Image
=========================

Idea
-----
- At build time, We configure the image through a regular makina-states (mc_project) based
  saltstack project.
- All the processes inside the container must be managed if possible via circus
- POSIX Acls are now avoided at all cost
- At run time:

    - the app is lightly reconfigured via salt and mau be given an
      overriden pillar file via a prebacked volume to help to reconfigure it.
    - Volumes and files that need to be prepolulated should be filled by the
      launcher if and only if it is not already done
    - The app is launched on foreground
    - A Control-C or quit signal must inhibit any launched process more or less
      gracefully

All those steps are done via a saltstack module that should be named
"mc_launcher" with a "launch" and a "reconfigure" method. This module is included in
the workflow via the mc_project "_modules" subdirectory.

layout inside the Image
-------------------------
This is of course an example but it reflects what we need to respect::

    /srv/salt/custom.sls      <- custom pillar
    /srv/projects/<project>
       |
       |- project/ <- application code
       |     |- Dockerfile       <- Each app needs to have a basic Dockerfile
       |     |- launch.sh        <- launcher that:
       |     |                      - copy $data/application/pillar.sls -> $pillar/init.sls and trigger
       |     |                      - reconfigure (via salt) the app
       |     |                      - launch the app in foreground
       |     |- .salt                 <- deployment and reconfigure code
       |     |- .salt/100_dirs_and_prerequisites.sls
       |     |- .salt/200_reconfigure.sls
       |     |- .salt/300_nginx.sls
       |     |- .salt/400_circus.sls
       |     |- .salt/_modules/mc_launcher.py <- code that is used to
       |                                         reconfigure the image at launch time (via launch.sh)
       |
       |- pillar/  <- salt extra pillar that overrides PILLAR.sample
       |
       |- data/                  <- exposed through a docker volume
             |- data/            <- persistent data root
             |- configuration/   <- deploy time pillar that is used at reconfigure
                                     time (startup of a pre-built image)
