#
# Apache Fine Settings ------------------------------------------------
# Timeout: The number of seconds before receives and sends time out. default is 300 (5min),
#          1 or 2 min should be enough for any client request (so 60 or 120). beware of DOS!
# KeepAlive: bool: are KeepAlive requests allowed
# MaxKeepAliveRequests: maximum number of allowed KeepAlive requests (compare with MaxClients)
# KeepAliveTimeout: How many seconds should we keep Keepalive conn open (say something between 3 and 5 usually, be careful for DOS!)
# log_level: log level, allowed values are debug, info, notice, warn, error, crit, alert, emerg
# serveradmin_mail: default webmaster mail (used on error pages)
# mpm prefork
#   * StartServers: number of server processes to start
#   * MinSpareServers: minimum number of server processes which are kept spare
#   * MaxSpareServers: maximum number of server processes which are kept spare
#   * MaxRequestsPerChild: maximum number of requests a server process serves
#                          set 0 to disable process recylcing
#   * MaxClients : (alias MaxRequestWorkers): maximum number of server processes allowed to start
# mpm worker
#   * StartServers: initial number of server processes to start
#   * MinSpareThreads: minimum number of worker threads which are kept spare
#   * MaxSpareThreads: maximum number of worker threads which are kept spare
#   * ThreadLimit: ThreadsPerChild can be changed to this maximum value during a
#             graceful restart. ThreadLimit can only be changed by stopping
#             and starting Apache.
#   * ThreadsPerChild: constant number of worker threads in each server process
#   * MaxRequestsPerChild (alias MaxConnectionsPerChild): maximum number of requests a server process serves
#                          set 0 to disable process recylcing
#   * MaxClients : (alias MaxRequestWorkers): maximum number of threads
# mpm event
#   * all workers settings are used
#   * AsyncRequestWorkerFactor: max of concurrent conn is (AsyncRequestWorkerFactor + 1) * MaxRequestWorkers

