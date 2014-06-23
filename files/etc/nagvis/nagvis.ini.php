; MANAGED VIA SALT -- DO NOT EDIT
{% set data = salt['mc_utils.json_load'](data) %}
; <?php return 1; ?>
; the line above is to prevent
; viewing this file from web.
; DON'T REMOVE IT!

; ----------------------------
; Default NagVis Configuration File
; At delivery everything here is commented out. The default values are set in the NagVis code.
; You can make your changes here, they'll overwrite the default settings.
; ----------------------------

; ----------------------------
; !!! The sections/variables with a leading ";" won't be recognised by NagVis (commented out) !!!
; ----------------------------

; General options which affect the whole NagVis installation
[global]
; Enable/Disable logging of security related user actions in Nagvis. For
; example user logins and logouts are logged in var/nagvis-audit.log
{% if data.nagvis_ini_php.global.get('audit_log', None) %}
audit_log="{{data.nagvis_ini_php.global.audit_log}}"
{% endif %}
;
; Defines the authentication module to use. By default NagVis uses the built-in
; SQLite authentication module. On delivery there is no other authentication
; module available. It is possible to add own authentication modules for
; supporting other authorisation mechanisms. For details take a look at the
; documentation.
{% if data.nagvis_ini_php.global.get('authmodule', None) %}
authmodule="{{data.nagvis_ini_php.global.authmodule}}"
{% endif %}
;
; Defines the authorisation module to use. By default NagVis uses the built-in
; SQLite authorisation module. On delivery there is no other authorisation
; module available. It is possible to add own authorisation modules for
; supporting other authorisation mechanisms. For details take a look at the
; documentation.
{% if data.nagvis_ini_php.global.get('authorisationmodule', None) %}
authorisationmodule="{{data.nagvis_ini_php.global.authorisationmodule}}"
{% endif %}
;
; Sets the size of the controls in unlocked (edit) mode of the frontend. This
; defaults to a value of 10 which makes each control be sized to 10px * 10px.
{% if data.nagvis_ini_php.global.get('controls_size', None) %}
controls_size="{{data.nagvis_ini_php.global.controls_size}}"
{% endif %}
;
; Dateformat of the time/dates shown in nagvis (For valid format see PHP docs)
{% if data.nagvis_ini_php.global.get('dateformat', None) %}
dateformat="{{data.nagvis_ini_php.global.dateformat}}"
{% endif %}
;
; Used to configure the preselected options in the "acknowledge problem" dialog
{% if data.nagvis_ini_php.global.get('dialog_ack_sticky', None) %}
dialog_ack_sticky="{{data.nagvis_ini_php.global.dialog_ack_sticky}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('dialog_ack_notify', None) %}
dialog_ack_notify="{{data.nagvis_ini_php.global.dialog_ack_notify}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('dialog_ack_persist', None) %}
dialog_ack_persist="{{data.nagvis_ini_php.global.dialog_ack_persist}}"
{% endif %}
;
; File group and mode are applied to all files which are written by NagVis.
; Usualy these values can be left as they are. In some rare cases you might
; want to change these values to make the files writeable/readable by some other
; users in a group.
{% if data.nagvis_ini_php.global.get('file_group', None) %}
file_group="{{data.nagvis_ini_php.global.file_group}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('file_mode', None) %}
file_mode="{{data.nagvis_ini_php.global.file_mode}}"
{% endif %}
;
; The server to use as source for the NagVis geomaps. Must implement the API which
; can be found on http://pafciu17.dev.openstreetmap.org/
{% if data.nagvis_ini_php.global.get('geomap_server', None) %}
geomap_server="{{data.nagvis_ini_php.global.geomap_server}}"
{% endif %}
;
; In some cases NagVis needs to open connections to the internet. The cases are:
; - The new geomap needs access to openstreetmap webservices to be able to fetch
;   mapping information
; Most company networks don't allow direct HTTP access to the internet. The most
; networks require the users to use proxy servers for outbound HTTP requests.
; The proxy url to be used in NagVis can be configured here. One possible value
; is "tcp://127.0.0.1:8080".
{% if data.nagvis_ini_php.global.get('http_proxy', None) %}
http_proxy="{{data.nagvis_ini_php.global.http_proxy}}"
{% endif %}
; Most proxies require authentication to access the internet. Use the format
; "<username>:<password>" to provide auth credentials
{% if data.nagvis_ini_php.global.get('http_proxy_auth', None) %}
http_proxy_auth="{{data.nagvis_ini_php.global.http_proxy_auth}}"
{% endif %}
; Set the timeout (in seconds) for outbound HTTP requests (for example geomap requests)
{% if data.nagvis_ini_php.global.get('http_timeout', None) %}
http_timeout="{{data.nagvis_ini_php.global.http_timeout}}"
{% endif %}
;
; Defines which translations of NagVis are available to the users
{% if data.nagvis_ini_php.global.get('language_available', None) %}
language_available="{{data.nagvis_ini_php.global.language_available}}"
{% endif %}
; Language detection steps to use. Available:
;  - User:    The user selection
;  - Session: Language saved in the session (Usually set after first setting an
;             explicit language)
;  - Browser: Detection by user agent information from the browser
;  - Config:  Use configured default language (See below)
{% if data.nagvis_ini_php.global.get('language_detection', None) %}
language_detection="{{data.nagvis_ini_php.global.language_detection}}"
{% endif %}
;
; Select language (Available by default: en_US, de_DE, fr_FR, pt_BR)
{% if data.nagvis_ini_php.global.get('language', None) %}
language="{{data.nagvis_ini_php.global.language}}"
{% endif %}
;
; Defines the logon module to use. There are three logon modules to be used by
; default. It is possible to add own logon modules for serving other dialogs or
; ways of logging in. For details take a look at the documentation.
;
; The delivered modules are:
;
; LogonMixed: The mixed logon module uses the LogonEnv module as default and
;   the LogonDialog module as fallback when LogonEnv returns no username. This
;   should fit the requirements of most environments.
;
; LogonDialog: This is an HTML logon dialog for requesting authentication
;   information from the user.
;
; LogonEnv: It is possible to realise a fully "trusted" authentication
;   mechanism like all previous NagVis versions used it before. This way the user
;   is not really authenticated with NagVis. NagVis trusts the provided username
;   implicitly. NagVis uses the configured environment variable to identify the
;   user. You can add several authentication mechanisms to your webserver,
;   starting from the basic authentication used by Nagios (.htaccess) to single
;   sign-on environments.
;   Simply set logonmodule to "LogonEnv", put the environment variable to use as
;   username to the option logonenvvar and tell the authentication module to
;   create users in the database when provided users does not exist. The option
;   logonenvcreaterole tells the module to assign the new user to a specific role
;   set to empty string to disable that behaviour.
;
; LogonMultisite: This module uses the authentication provided by auth_* cookies
;   which have been generated by Check_MK multisite when using the cookie based
;   authentication. Since 1.2.1i2 Check_MK uses a new cookie format. To be able
;   to use this, you need to define a new option called logon_multisite_serials
;   which points to the auth.serial file generated by Check_MK.
;   Special options for this module:
;
;
{% if data.nagvis_ini_php.global.get('logonmodule', None) %}
logonmodule="{{data.nagvis_ini_php.global.logonmodule}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('logonenvvar', None) %}
logonenvvar="{{data.nagvis_ini_php.global.logonenvvar}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('logonenvcreateuser', None) %}
logonenvcreateuser="{{data.nagvis_ini_php.global.logonenvcreateuser}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('logonenvcreaterole', None) %}
logonenvcreaterole="{{data.nagvis_ini_php.global.logonenvcreaterole}}"
{% endif %}
;
; Default rotation time of pages in rotations
{% if data.nagvis_ini_php.global.get('refreshtime', None) %}
refreshtime="{{data.nagvis_ini_php.global.refreshtime}}"
{% endif %}
;
; Some user information is stored in sessions which are identified by session
; cookies placed on the users computer. The options below set the properties
; of the session cookie.
; Domain to set the cookie for. By default NagVis tries to auto-detect this
; options value by using the webserver's environment variables.
{% if data.nagvis_ini_php.global.get('sesscookiedomain', None) %}
sesscookiedomain="{{data.nagvis_ini_php.global.sesscookiedomain}}"
{% endif %}
; Absolute web path to set the cookie for. This defaults to configured
; paths/htmlbase option
{% if data.nagvis_ini_php.global.get('sesscookiepath', None) %}
sesscookiepath="{{data.nagvis_ini_php.global.sesscookiepath}}"
{% endif %}
; Lifetime of the NagVis session cookie in seconds. The default value is set to
; 24 hours. The NagVis session cookie contents will be renewed on every page
; visit. If a session is idle for more time than configured here it will become
; invalid.
{% if data.nagvis_ini_php.global.get('sesscookieduration', None) %}
sesscookieduration="{{data.nagvis_ini_php.global.sesscookieduration}}"
{% endif %}
;
; Start page to redirect the user to when first visiting NagVis without
; special parameters.
{% if data.nagvis_ini_php.global.get('startmodule', None) %}
startmodule="{{data.nagvis_ini_php.global.startmodule}}"
{% endif %}
{% if data.nagvis_ini_php.global.get('startaction', None) %}
startaction="{{data.nagvis_ini_php.global.startaction}}"
{% endif %}
; The startshow parameter is only used by some views at the moment. It is used
; by the Map module.
{% if data.nagvis_ini_php.global.get('startshow', None) %}
startshow="{{data.nagvis_ini_php.global.startshow}}"
{% endif %}
;
; Turn on to enable some shinken related features in NagVis, like the
; min_business_impact-filter on automaps which can be used to render automaps
; based on the shinken attribute "business_impact".
{% if data.nagvis_ini_php.global.get('shinken_features', None) %}
shinken_features="{{data.nagvis_ini_php.global.shinken_features}}"
{% endif %}

; Path definitions
[paths]
; absolute physical NagVis path
{% if data.nagvis_ini_php.paths.get('base', None) %}
base="{{data.nagvis_ini_php.paths.base}}"
{% endif %}
; absolute html NagVis path
{% if data.nagvis_ini_php.paths.get('htmlbase', None) %}
htmlbase="{{data.nagvis_ini_php.paths.htmlbase}}"
{% endif %}
; absolute html NagVis cgi path
{% if data.nagvis_ini_php.paths.get('htmlcgi', None) %}
htmlcgi="{{data.nagvis_ini_php.paths.htmlcgi}}"
{% endif %}

; Default values which get inherited to the maps and its objects
[defaults]
; default backend (id of the default backend)
{% if data.nagvis_ini_php.defaults.get('backend', None) %}
backend="{{data.nagvis_ini_php.defaults.backend}}"
{% endif %}
; background color of maps
{% if data.nagvis_ini_php.defaults.get('backgroundcolor', None) %}
backgroundcolor="{{data.nagvis_ini_php.defaults.backgroundcolor}}"
{% endif %}
; Enable/Disable the context menu on map objects. With the context menu you are
; able to bind commands or links to your map objects
{% if data.nagvis_ini_php.defaults.get('contextmenu', None) %}
contextmenu="{{data.nagvis_ini_php.defaults.contextmenu}}"
{% endif %}
; Choose the default context template
{% if data.nagvis_ini_php.defaults.get('contexttemplate', None) %}
contexttemplate="{{data.nagvis_ini_php.defaults.contexttemplate}}"
{% endif %}
; Raise frontend events for problematic objects also on page loading. Set to 1 to
; enable this feature
{% if data.nagvis_ini_php.defaults.get('event_on_load', None) %}
event_on_load="{{data.nagvis_ini_php.defaults.event_on_load}}"
{% endif %}
; Repeat frontend events in the given interval. The interval is configured in seconds.
{% if data.nagvis_ini_php.defaults.get('event_repeat_interval', None) %}
event_repeat_interval="{{data.nagvis_ini_php.defaults.event_repeat_interval}}"
{% endif %}
; The time in seconds to repeat alerts for a problematic ojects for as configured in
; event_repeat_interval. This value defaults to -1, this leads to repeated events
; till the problematic state has been fixed.
{% if data.nagvis_ini_php.defaults.get('event_repeat_duration', None) %}
event_repeat_duration="{{data.nagvis_ini_php.defaults.event_repeat_duration}}"
{% endif %}
; Enable/Disable changing background color on state changes (Configured color is
; shown when summary state is PENDING, OK or UP)
{% if data.nagvis_ini_php.defaults.get('eventbackground', None) %}
eventbackground="{{data.nagvis_ini_php.defaults.eventbackground}}"
{% endif %}
; Enable/Disable highlighting of the state changing object by adding a flashing
; border
{% if data.nagvis_ini_php.defaults.get('eventhighlight', None) %}
eventhighlight="{{data.nagvis_ini_php.defaults.eventhighlight}}"
{% endif %}
; The duration of the event highlight in milliseconds (10 seconds by default)
{% if data.nagvis_ini_php.defaults.get('eventhighlightduration', None) %}
eventhighlightduration="{{data.nagvis_ini_php.defaults.eventhighlightduration}}"
{% endif %}
; The interval of the event highlight in milliseconds (0.5 seconds by default)
{% if data.nagvis_ini_php.defaults.get('eventhighlightinterval', None) %}
eventhighlightinterval="{{data.nagvis_ini_php.defaults.eventhighlightinterval}}"
{% endif %}
; Enable/Disable the eventlog in the new javascript frontend. The eventlog keeps
; track of important actions and information
{% if data.nagvis_ini_php.defaults.get('eventlog', None) %}
eventlog="{{data.nagvis_ini_php.defaults.eventlog}}"
{% endif %}
; Loglevel of the eventlog (available: debug, info, warning, critical)
{% if data.nagvis_ini_php.defaults.get('eventloglevel', None) %}
eventloglevel="{{data.nagvis_ini_php.defaults.eventloglevel}}"
{% endif %}
; Number of events kept in the scrollback
{% if data.nagvis_ini_php.defaults.get('eventlogevents', None) %}
eventlogevents="{{data.nagvis_ini_php.defaults.eventlogevents}}"
{% endif %}
; Height of the eventlog when visible in px
{% if data.nagvis_ini_php.defaults.get('eventlogheight', None) %}
eventlogheight="{{data.nagvis_ini_php.defaults.eventlogheight}}"
{% endif %}
; Hide/Show the eventlog on page load
{% if data.nagvis_ini_php.defaults.get('eventloghidden', None) %}
eventloghidden="{{data.nagvis_ini_php.defaults.eventloghidden}}"
{% endif %}
; Enable/Disable scrolling to the icon which changed the state when the icon is
; out of the visible scope
{% if data.nagvis_ini_php.defaults.get('eventscroll', None) %}
eventscroll="{{data.nagvis_ini_php.defaults.eventscroll}}"
{% endif %}
; Enable/Disable sound signals on state changes
{% if data.nagvis_ini_php.defaults.get('eventsound', None) %}
eventsound="{{data.nagvis_ini_php.defaults.eventsound}}"
{% endif %}
; enable/disable header menu
{% if data.nagvis_ini_php.defaults.get('headermenu', None) %}
headermenu="{{data.nagvis_ini_php.defaults.headermenu}}"
{% endif %}
; header template
{% if data.nagvis_ini_php.defaults.get('headertemplate', None) %}
headertemplate="{{data.nagvis_ini_php.defaults.headertemplate}}"
{% endif %}
; Enable/Diable the fading effect of the submenus in the header menu
{% if data.nagvis_ini_php.defaults.get('headerfade', None) %}
headerfade="{{data.nagvis_ini_php.defaults.headerfade}}"
{% endif %}
; enable/disable hover menu
{% if data.nagvis_ini_php.defaults.get('hovermenu', None) %}
hovermenu="{{data.nagvis_ini_php.defaults.hovermenu}}"
{% endif %}
; hover template
{% if data.nagvis_ini_php.defaults.get('hovertemplate', None) %}
hovertemplate="{{data.nagvis_ini_php.defaults.hovertemplate}}"
{% endif %}
; hover menu open delay (seconds)
{% if data.nagvis_ini_php.defaults.get('hoverdelay', None) %}
hoverdelay="{{data.nagvis_ini_php.defaults.hoverdelay}}"
{% endif %}
; show children in hover menus
{% if data.nagvis_ini_php.defaults.get('hoverchildsshow', None) %}
hoverchildsshow="{{data.nagvis_ini_php.defaults.hoverchildsshow}}"
{% endif %}
; limit shown child objects to n
{% if data.nagvis_ini_php.defaults.get('hoverchildslimit', None) %}
hoverchildslimit="{{data.nagvis_ini_php.defaults.hoverchildslimit}}"
{% endif %}
; order method of children (desc: descending, asc: ascending)
{% if data.nagvis_ini_php.defaults.get('hoverchildsorder', None) %}
hoverchildsorder="{{data.nagvis_ini_php.defaults.hoverchildsorder}}"
{% endif %}
; sort method of children (s: state, a: alphabetical)
{% if data.nagvis_ini_php.defaults.get('hoverchildssort', None) %}
hoverchildssort="{{data.nagvis_ini_php.defaults.hoverchildssort}}"
{% endif %}
; default icons
{% if data.nagvis_ini_php.defaults.get('icons', None) %}
icons="{{data.nagvis_ini_php.defaults.icons}}"
{% endif %}
; recognize only hard states (not soft)
{% if data.nagvis_ini_php.defaults.get('onlyhardstates', None) %}
onlyhardstates="{{data.nagvis_ini_php.defaults.onlyhardstates}}"
{% endif %}
; recognize service states in host/hostgroup objects
{% if data.nagvis_ini_php.defaults.get('recognizeservices', None) %}
recognizeservices="{{data.nagvis_ini_php.defaults.recognizeservices}}"
{% endif %}
; show map in lists (dropdowns, index page, ...)
{% if data.nagvis_ini_php.defaults.get('showinlists', None) %}
showinlists="{{data.nagvis_ini_php.defaults.showinlists}}"
{% endif %}
; show map in multisite snapin
{% if data.nagvis_ini_php.defaults.get('showinmultisite', None) %}
showinmultisite="{{data.nagvis_ini_php.defaults.showinmultisite}}"
{% endif %}
; Name of the custom stylesheet to use on the maps (The file needs to be located
; in the share/nagvis/styles directory)
{% if data.nagvis_ini_php.defaults.get('stylesheet', None) %}
stylesheet="{{data.nagvis_ini_php.defaults.stylesheet}}"
{% endif %}
; target for the icon links
{% if data.nagvis_ini_php.defaults.get('urltarget', None) %}
urltarget="{{data.nagvis_ini_php.defaults.urltarget}}"
{% endif %}
; URL template for host object links
{% if data.nagvis_ini_php.defaults.get('hosturl', None) %}
hosturl="{{data.nagvis_ini_php.defaults.hosturl}}"
{% endif %}
; URL template for hostgroup object links
{% if data.nagvis_ini_php.defaults.get('hostgroupurl', None) %}
hostgroupurl="{{data.nagvis_ini_php.defaults.hostgroupurl}}"
{% endif %}
; URL template for service object links
{% if data.nagvis_ini_php.defaults.get('serviceurl', None) %}
serviceurl="{{data.nagvis_ini_php.defaults.serviceurl}}"
{% endif %}
; URL template for servicegroup object links
{% if data.nagvis_ini_php.defaults.get('servicegroupurl', None) %}
servicegroupurl="{{data.nagvis_ini_php.defaults.servicegroupurl}}"
{% endif %}
; URL template for nested map links
{% if data.nagvis_ini_php.defaults.get('mapurl', None) %}
mapurl="{{data.nagvis_ini_php.defaults.mapurl}}"
{% endif %}
; Templates to be used for the different views.
{% if data.nagvis_ini_php.defaults.get('view_template', None) %}
view_template="{{data.nagvis_ini_php.defaults.view_template}}"
{% endif %}
; Enable/disable object labels for all objects
{% if data.nagvis_ini_php.defaults.get('label_show', None) %}
label_show="{{data.nagvis_ini_php.defaults.label_show}}"
{% endif %}
; Configure the colors used by weathermap lines
{% if data.nagvis_ini_php.defaults.get('line_weather_colors', None) %}
line_weather_colors="{{data.nagvis_ini_php.defaults.line_weather_colors}}"
{% endif %}

; Options to configure the Overview page of NagVis
[index]
; Color of the overview background
{% if data.nagvis_ini_php.index.get('backgroundcolor', None) %}
backgroundcolor="{{data.nagvis_ini_php.index.backgroundcolor}}"
{% endif %}
; Set number of map cells per row
{% if data.nagvis_ini_php.index.get('cellsperrow', None) %}
cellsperrow="{{data.nagvis_ini_php.index.cellsperrow}}"
{% endif %}
; enable/disable header menu
{% if data.nagvis_ini_php.index.get('headermenu', None) %}
headermenu="{{data.nagvis_ini_php.index.headermenu}}"
{% endif %}
; header template
{% if data.nagvis_ini_php.index.get('headertemplate', None) %}
headertemplate="{{data.nagvis_ini_php.index.headertemplate}}"
{% endif %}
; Enable/Disable map listing
{% if data.nagvis_ini_php.index.get('showmaps', None) %}
showmaps="{{data.nagvis_ini_php.index.showmaps}}"
{% endif %}
; Enable/Disable geomap listing
;   Note: It is disabled here since it is unfinished yet and not for production
;         use in current 1.5 code.
{% if data.nagvis_ini_php.index.get('showgeomap', None) %}
showgeomap="{{data.nagvis_ini_php.index.showgeomap}}"
{% endif %}
; Enable/Disable rotation listing
{% if data.nagvis_ini_php.index.get('showrotations', None) %}
showrotations="{{data.nagvis_ini_php.index.showrotations}}"
{% endif %}
; Enable/Disable map thumbnails
{% if data.nagvis_ini_php.index.get('showmapthumbs', None) %}
showmapthumbs="{{data.nagvis_ini_php.index.showmapthumbs}}"
{% endif %}

; Options for the Automap
[automap]
; Default URL parameters for links to the automap
{% if data.nagvis_ini_php.automap.get('defaultparams', None) %}
defaultparams="{{data.nagvis_ini_php.automap.defaultparams}}"
{% endif %}
; Default root host (NagVis uses this if it can't detect it via backend)
; You can configure a hostname here or use "<<<monitoring>>>" as "virtual"
; node which shows the parent tree and all hosts which have no parents
; defined below the is node.
{% if data.nagvis_ini_php.automap.get('defaultroot', None) %}
defaultroot="{{data.nagvis_ini_php.automap.defaultroot}}"
{% endif %}
; Path to the graphviz binaries (dot,neato,...); Only needed if not in ENV PATH
{% if data.nagvis_ini_php.automap.get('graphvizpath', None) %}
graphvizpath="{{data.nagvis_ini_php.automap.graphvizpath}}"
{% endif %}

; Options for the WUI
[wui]
; map lock time (minutes). When a user edits a map other users trying to edit
; the map are warned about this fact.
{% if data.nagvis_ini_php.wui.get('maplocktime', None) %}
maplocktime="{{data.nagvis_ini_php.wui.maplocktime}}"
{% endif %}
; Show/hide the grid
{% if data.nagvis_ini_php.wui.get('grid_show', None) %}
grid_show="{{data.nagvis_ini_php.wui.grid_show}}"
{% endif %}
; The color of the grid lines
{% if data.nagvis_ini_php.wui.get('grid_color', None) %}
grid_color="{{data.nagvis_ini_php.wui.grid_color}}"
{% endif %}
; The space between the single grid lines in pixels
{% if data.nagvis_ini_php.wui.get('grid_steps', None) %}
grid_steps="{{data.nagvis_ini_php.wui.grid_steps}}"
{% endif %}

; Options for the new Javascript worker
[worker]
; The interval in seconds in which the worker will check for objects which need
; to be updated
{% if data.nagvis_ini_php.worker.get('interval', None) %}
interval="{{data.nagvis_ini_php.worker.interval}}"
{% endif %}
; The maximum number of parameters used in ajax http requests
; Some intrusion detection/prevention systems have a problem with
; too many parameters in the url. Give 0 for no limit.
{% if data.nagvis_ini_php.worker.get('requestmaxparams', None) %}
requestmaxparams="{{data.nagvis_ini_php.worker.requestmaxparams}}"
{% endif %}
; The maximum length of http request urls during ajax http requests
; Some intrusion detection/prevention systems have a problem with
; queries being too long
{% if data.nagvis_ini_php.worker.get('requestmaxlength', None) %}
requestmaxlength="{{data.nagvis_ini_php.worker.requestmaxlength}}"
{% endif %}
; The retention time of the states in the frontend in seconds. The state
; information will be refreshed after this time
{% if data.nagvis_ini_php.worker.get('updateobjectstates', None) %}
updateobjectstates="{{data.nagvis_ini_php.worker.updateobjectstates}}"
{% endif %}

; ----------------------------
; Backend definitions
; ----------------------------

{% if data.nagvis_ini_php.get('backends', None) %}
{% for name,backend in data.nagvis_ini_php.backends.items() %}
[backend_{{name}}]

{% for key,value in backend.items() %}
{{key}}="{{value}}"

{% endfor %}
{% endfor %}
{% endif %}

; ----------------------------
; Rotation pool definitions
; ----------------------------

{% if data.nagvis_ini_php.get('rotations', None) %}
{% for name,rotation in data.nagvis_ini_php.rotations.items() %}
[rotation_{{name}}]

{% for key,value in rotation.items() %}
{{key}}="{{value}}"

{% endfor %}
{% endfor %}
{% endif %}

; ----------------------------
; Action definitions
; ----------------------------
; Since NagVis 1.7.6 it is possible to use so called actions to extend the
; default context menu. This enables users to connect directly to the monitored
; hosts from the NagVis context menu. Here you can configure those actions.
;
; It is possible to add such actions to the context menus of service and host
; objects. They are not added blindly to all objects of those types, you can
; use the attribute "condition" to configure which objects shal have the
; specific actions. By default we use Nagios custom macros of the host object
; to make the actions visible/invisible. This filtering mechanism is not limited
; to custom macros, you can also use regular host attributes which are available
; within NagVis.
; With the option "client_os" you can configure the option to only be available
; on the clients which have a listed operating system running.

; Adds the action "connect via rdp" to service/host objects where the host object
; has the string "win" in the TAGS Nagios custom macro.
; When clicking on the link, NagVis generates a .rdp file which contains makes
; the client connect to the given host via RDP.
{% if data.nagvis_ini_php.get('actions', None) %}
{% for name,action in data.nagvis_ini_php.actions.items() %}
[action_{{name}}]

{% for key,value in action.items() %}
{{key}}="{{value}}"

{% endfor %}
{% endfor %}
{% endif %}

; ------------------------------------------------------------------------------
; Below you find some advanced stuff
; ------------------------------------------------------------------------------

; Configure different state related settings
[states]
; State coverage/weight: This defines the state handling behaviour. For example
; a critical state will cover a warning state and an acknowledged critical
; state will not cover a warning state.
;
; These options are being used when calculating the summary state of the map
; objects. The default values should fit most needs.
;
{% if data.nagvis_ini_php.states.get('down', None) %}
down="{{data.nagvis_ini_php.states.down}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_ack', None) %}
down_ack="{{data.nagvis_ini_php.states.down_ack}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_downtime', None) %}
down_downtime="{{data.nagvis_ini_php.states.down_downtime}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unreachable', None) %}
unreachable="{{data.nagvis_ini_php.states.unreachable}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unreachable_ack', None) %}
unreachable_ack="{{data.nagvis_ini_php.states.unreachable_ack}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unreachable_downtime', None) %}
unreachable_downtime="{{data.nagvis_ini_php.states.unreachable_downtime}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical', None) %}
critical="{{data.nagvis_ini_php.states.critical}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_ack', None) %}
critical_ack="{{data.nagvis_ini_php.states.critical_ack}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_downtime', None) %}
critical_downtime="{{data.nagvis_ini_php.states.critical_downtime}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning', None) %}
warning="{{data.nagvis_ini_php.states.warning}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_ack', None) %}
warning_ack="{{data.nagvis_ini_php.states.warning_ack}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_downtime', None) %}
warning_downtime="{{data.nagvis_ini_php.states.warning_downtime}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown', None) %}
unknown="{{data.nagvis_ini_php.states.unknown}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_ack', None) %}
unknown_ack="{{data.nagvis_ini_php.states.unknown_ack}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_downtime', None) %}
unknown_downtime="{{data.nagvis_ini_php.states.unknown_downtime}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('error', None) %}
error="{{data.nagvis_ini_php.states.error}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('error_ack', None) %}
error_ack="{{data.nagvis_ini_php.states.error_ack}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('error_downtime', None) %}
error_downtime="{{data.nagvis_ini_php.states.error_downtime}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('up', None) %}
up="{{data.nagvis_ini_php.states.up}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('ok', None) %}
ok="{{data.nagvis_ini_php.states.ok}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unchecked', None) %}
unchecked="{{data.nagvis_ini_php.states.unchecked}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('pending', None) %}
pending="{{data.nagvis_ini_php.states.pending}}"
{% endif %}
;
; Colors of the different states. The colors are used in lines and hover menus
; and for example in the frontend highlight and background event handler
;
{% if data.nagvis_ini_php.states.get('unreachable_bgcolor', None) %}
unreachable_bgcolor="{{data.nagvis_ini_php.states.unreachable_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unreachable_color', None) %}
unreachable_color="{{data.nagvis_ini_php.states.unreachable_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unreachable_ack_bgcolor', None) %}
unreachable_ack_bgcolor="{{data.nagvis_ini_php.states.unreachable_ack_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unreachable_downtime_bgcolor', None) %}
unreachable_downtime_bgcolor="{{data.nagvis_ini_php.states.unreachable_downtime_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_bgcolor', None) %}
down_bgcolor="{{data.nagvis_ini_php.states.down_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_color', None) %}
down_color="{{data.nagvis_ini_php.states.down_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_ack_bgcolor', None) %}
down_ack_bgcolor="{{data.nagvis_ini_php.states.down_ack_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_downtime_bgcolor', None) %}
down_downtime_bgcolor="{{data.nagvis_ini_php.states.down_downtime_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_bgcolor', None) %}
critical_bgcolor="{{data.nagvis_ini_php.states.critical_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_color', None) %}
critical_color="{{data.nagvis_ini_php.states.critical_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_ack_bgcolor', None) %}
critical_ack_bgcolor="{{data.nagvis_ini_php.states.critical_ack_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_downtime_bgcolor', None) %}
critical_downtime_bgcolor="{{data.nagvis_ini_php.states.critical_downtime_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_bgcolor', None) %}
warning_bgcolor="{{data.nagvis_ini_php.states.warning_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_color', None) %}
warning_color="{{data.nagvis_ini_php.states.warning_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_ack_bgcolor', None) %}
warning_ack_bgcolor="{{data.nagvis_ini_php.states.warning_ack_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_downtime_bgcolor', None) %}
warning_downtime_bgcolor="{{data.nagvis_ini_php.states.warning_downtime_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_bgcolor', None) %}
unknown_bgcolor="{{data.nagvis_ini_php.states.unknown_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_color', None) %}
unknown_color="{{data.nagvis_ini_php.states.unknown_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_ack_bgcolor', None) %}
unknown_ack_bgcolor="{{data.nagvis_ini_php.states.unknown_ack_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_downtime_bgcolor', None) %}
unknown_downtime_bgcolor="{{data.nagvis_ini_php.states.unknown_downtime_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('error_bgcolor', None) %}
error_bgcolor="{{data.nagvis_ini_php.states.error_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('error_color', None) %}
error_color="{{data.nagvis_ini_php.states.error_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('up_bgcolor', None) %}
up_bgcolor="{{data.nagvis_ini_php.states.up_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('up_color', None) %}
up_color="{{data.nagvis_ini_php.states.up_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('ok_bgcolor', None) %}
ok_bgcolor="{{data.nagvis_ini_php.states.ok_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('ok_color', None) %}
ok_color="{{data.nagvis_ini_php.states.ok_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unchecked_bgcolor', None) %}
unchecked_bgcolor="{{data.nagvis_ini_php.states.unchecked_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unchecked_color', None) %}
unchecked_color="{{data.nagvis_ini_php.states.unchecked_color}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('pending_bgcolor', None) %}
pending_bgcolor="{{data.nagvis_ini_php.states.pending_bgcolor}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('pending_color', None) %}
pending_color="{{data.nagvis_ini_php.states.pending_color}}"
{% endif %}
;
; Sound of the different states to be used by the sound eventhandler in the
; frontend. The sounds are only being fired when changing to some
; worse state.
;
{% if data.nagvis_ini_php.states.get('unreachable_sound', None) %}
unreachable_sound="{{data.nagvis_ini_php.states.unreachable_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('down_sound', None) %}
down_sound="{{data.nagvis_ini_php.states.down_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('critical_sound', None) %}
critical_sound="{{data.nagvis_ini_php.states.critical_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('warning_sound', None) %}
warning_sound="{{data.nagvis_ini_php.states.warning_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unknown_sound', None) %}
unknown_sound="{{data.nagvis_ini_php.states.unknown_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('error_sound', None) %}
error_sound="{{data.nagvis_ini_php.states.error_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('up_sound', None) %}
up_sound="{{data.nagvis_ini_php.states.up_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('ok_sound', None) %}
ok_sound="{{data.nagvis_ini_php.states.ok_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('unchecked_sound', None) %}
unchecked_sound="{{data.nagvis_ini_php.states.unchecked_sound}}"
{% endif %}
{% if data.nagvis_ini_php.states.get('pending_sound', None) %}
pending_sound="{{data.nagvis_ini_php.states.pending_sound}}"
{% endif %}

; -------------------------
; EOF
; -------------------------
