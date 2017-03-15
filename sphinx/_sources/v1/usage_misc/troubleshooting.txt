Troubleshooting
=================
::

    Generated script '/srv/salt/makina-states/bin/buildout'.
    Launching buildout for salt initialisation
    Traceback (most recent call last):
      File "bin/buildout", line 17, in <module>
        import zc.buildout.buildout
      File "/srv/salt/makina-states/eggs/zc.buildout-1.7.1-py2.7.egg/zc/buildout/buildout.py", line 40, in <module>
        import zc.buildout.download
      File "/srv/salt/makina-states/eggs/zc.buildout-1.7.1-py2.7.egg/zc/buildout/download.py", line 20, in <module>
        from zc..buildout.easy_install import realpath
      File "/srv/salt/makina-states/eggs/zc.buildout-1.7.1-py2.7.egg/zc/buildout/easy_install.py", line 31, in <module>
        import setuptools.package_index
      File "/usr/local/lib/python2.7/dist-packages/distribute-0.6.24-py2.7.egg/setuptools/package_index.py", line 157, in <module>
        sys.version[:3], require('distribute')[0].version
      File "build/bdist.linux-x86_64/egg/pkg_resources.py", line 728, in require
        supplied, ``sys.path`` is used.
      File "build/bdist.linux-x86_64/egg/pkg_resources.py", line 626, in resolve
        ``VersionConflict`` instance.
    pkg_resources.DistributionNotFound: distribute
    Failed buildout

Update your system setuptools install to match latest setuptools (distribute + setuptools fork reunion)::

    sudo easy_install -U setuptools



