Tomcat configuration
====================
By default, we will use the java6 oracle jdk jvm.

For example::

    makina-states.services.java.tomcat7:
         java_home': /usr/lib/jvm/java-6-oracle
     users:
       admin:
         password: {{ password }}
         roles': ['admin', 'manager']

AVAILABLE DEFAULT SETTINGS
---------------------------
You can override default settings in pillar via the mc_states.tomcat module, please look its relative doc.

CUSTOM CONFIGURATION BLOCKS
----------------------------
Thanks to file.blockreplace + file.accumulated, you can also add on the fly raw tomcat configuration blocks.
Custom configuration blocks have been wired on those files:

  - server.xml
  - context.xml
  - web.xml
  - logging.properties
  - {{ locs.conf_dir }}/default/tomcat7 (practical to add
    JAVA_OPTS addition from other sls (eg adding solr datadir & home properties)
  - catalina.properties

See at the end of this state file for the appropriate blockreplace to use
in your case and where those block are located in the aforementioned files.
What you will need is just to make a file.accumulated requirin the appropriate
file.blockreplace ID to add your configuration block.


Exposed state orchestration hooks
----------------------------------
Hooks (in order):

tomcat-pre-install-hook
    before tomcat installation
tomcat-post-install-hook
    after tomcat installation
tomcat-pre-restart-hook
    before tomcat restart (after install)
tomcat-pre-blocks-hook:
    before applying block replaces in configuration files
tomcat-post-restart-hook
    after tomcat restart



