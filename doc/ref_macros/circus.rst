Macros
------
You can use the circusAddWatcher macro to add a watcher:

    circusAddWatcher(name, cmd, \*\*kwargs)

* name: name of the watcher
* cmd: command to execute and to monitor
* any keyword argument is putted inside the watcher definition in the circus configuration file

    * SPECIAL CMD LINE ARGS:
      :args: arguments of cmdline
      :conf_priority: special keyword to specify the file order priority in configuration directory


