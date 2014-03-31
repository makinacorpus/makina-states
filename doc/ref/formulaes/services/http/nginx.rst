Nginx
=====

- This integrates configure and tune the fast http nginx server.
- Please have a loop to :ref:`mc_nginx` to know all configuration options.
- We have take a spetial care to try to tune it some a good production usage
start.
- In our own particular setup, nginx is served by a frontal haproxy reverse proxy.

Please note that we offer a spetial macro to generate virtualhosts and manage
their activation.
Look at `here <https://github.com/makinacorpus/makina-states/blob/master/services/http/nginx/vhosts.sls>`_.

Sites are enabled and deactivated a la debian, with the /etc/nginx/sites-{available/deactivated} directories.
::

  {% import "makina-states/services/http/nginx/vhosts.sls" as nvh with context %}
  vhostbody:
    file.managed:
        - name: /srv/salt/body.domain.com
        - source: ''
        - contents: |
                    redirect_permanent: google.fr
  {{nvh.virtualhost('domain.com',
                     vhost_content_template='salt://body.domain.com') }}

You can also register new sites in pillar to avoid calling manually the macro.
pillar example::

    makina-states.services.http.nginx.virtualhosts.example.com:
        active: False
        small_name: example
        documentRoot: /srv/foo/bar/www
    makina-states.services.http.nginx.virtualhosts.example.foo.com:
        active: False
        port: 8080
        server_aliases:
          - bar.foo.com

Note that the best way to make a VH is not the pillar, but
loading the macro as we do here and use virtualhost()) call
in a state.
Then use the pillar to alter your default parameters given to this call

 
