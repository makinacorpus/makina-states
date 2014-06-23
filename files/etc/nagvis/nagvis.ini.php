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

audit_log="{{data.nagvis_ini_php.global.audit_log}}"

;
; Defines the authentication module to use. By default NagVis uses the built-in
; SQLite authentication module. On delivery there is no other authentication
; module available. It is possible to add own authentication modules for
; supporting other authorisation mechanisms. For details take a look at the
; documentation.

authmodule="{{data.nagvis_ini_php.global.authmodule}}"

;
; Defines the authorisation module to use. By default NagVis uses the built-in
; SQLite authorisation module. On delivery there is no other authorisation
; module available. It is possible to add own authorisation modules for
; supporting other authorisation mechanisms. For details take a look at the
; documentation.

authorisationmodule="{{data.nagvis_ini_php.global.authorisationmodule}}"

;
; Sets the size of the controls in unlocked (edit) mode of the frontend. This
; defaults to a value of 10 which makes each control be sized to 10px * 10px.

controls_size="{{data.nagvis_ini_php.global.controls_size}}"

;
; Dateformat of the time/dates shown in nagvis (For valid format see PHP docs)

dateformat="{{data.nagvis_ini_php.global.dateformat}}"

;
; Used to configure the preselected options in the "acknowledge problem" dialog

dialog_ack_sticky="{{data.nagvis_ini_php.global.dialog_ack_sticky}}"


dialog_ack_notify="{{data.nagvis_ini_php.global.dialog_ack_notify}}"


dialog_ack_persist="{{data.nagvis_ini_php.global.dialog_ack_persist}}"

;
; File group and mode are applied to all files which are written by NagVis.
; Usualy these values can be left as they are. In some rare cases you might
; want to change these values to make the files writeable/readable by some other
; users in a group.

file_group="{{data.nagvis_ini_php.global.file_group}}"


file_mode="{{data.nagvis_ini_php.global.file_mode}}"

;
; The server to use as source for the NagVis geomaps. Must implement the API which
; can be found on http://pafciu17.dev.openstreetmap.org/

geomap_server="{{data.nagvis_ini_php.global.geomap_server}}"

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

http_timeout="{{data.nagvis_ini_php.global.http_timeout}}"

;
; Defines which translations of NagVis are available to the users

language_available="{{data.nagvis_ini_php.global.language_available}}"

; Language detection steps to use. Available:
;  - User:    The user selection
;  - Session: Language saved in the session (Usually set after first setting an
;             explicit language)
;  - Browser: Detection by user agent information from the browser
;  - Config:  Use configured default language (See below)

language_detection="{{data.nagvis_ini_php.global.language_detection}}"

;
; Select language (Available by default: en_US, de_DE, fr_FR, pt_BR)

language="{{data.nagvis_ini_php.global.language}}"

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

logonmodule="{{data.nagvis_ini_php.global.logonmodule}}"


logonenvvar="{{data.nagvis_ini_php.global.logonenvvar}}"


logonenvcreateuser="{{data.nagvis_ini_php.global.logonenvcreateuser}}"


logonenvcreaterole="{{data.nagvis_ini_php.global.logonenvcreaterole}}"

;
; Default rotation time of pages in rotations

refreshtime="{{data.nagvis_ini_php.global.refreshtime}}"

;
; Some user information is stored in sessions which are identified by session
; cookies placed on the users computer. The options below set the properties
; of the session cookie.
; Domain to set the cookie for. By default NagVis tries to auto-detect this
; options value by using the webserver's environment variables.

sesscookiedomain="{{data.nagvis_ini_php.global.sesscookiedomain}}"

; Absolute web path to set the cookie for. This defaults to configured
; paths/htmlbase option

sesscookiepath="{{data.nagvis_ini_php.global.sesscookiepath}}"

; Lifetime of the NagVis session cookie in seconds. The default value is set to
; 24 hours. The NagVis session cookie contents will be renewed on every page
; visit. If a session is idle for more time than configured here it will become
; invalid.

sesscookieduration="{{data.nagvis_ini_php.global.sesscookieduration}}"

;
; Start page to redirect the user to when first visiting NagVis without
; special parameters.

startmodule="{{data.nagvis_ini_php.global.startmodule}}"


startaction="{{data.nagvis_ini_php.global.startaction}}"

; The startshow parameter is only used by some views at the moment. It is used
; by the Map module.

startshow="{{data.nagvis_ini_php.global.startshow}}"

;
; Turn on to enable some shinken related features in NagVis, like the
; min_business_impact-filter on automaps which can be used to render automaps
; based on the shinken attribute "business_impact".

shinken_features="{{data.nagvis_ini_php.global.shinken_features}}"


; Path definitions
[paths]
; absolute physical NagVis path

base="{{data.nagvis_ini_php.paths.base}}"

; absolute html NagVis path

htmlbase="{{data.nagvis_ini_php.paths.htmlbase}}"

; absolute html NagVis cgi path

htmlcgi="{{data.nagvis_ini_php.paths.htmlcgi}}"


; Default values which get inherited to the maps and its objects
[defaults]
; default backend (id of the default backend)

backend="{{data.nagvis_ini_php.defaults.backend}}"

; background color of maps

backgroundcolor="{{data.nagvis_ini_php.defaults.backgroundcolor}}"

; Enable/Disable the context menu on map objects. With the context menu you are
; able to bind commands or links to your map objects

contextmenu="{{data.nagvis_ini_php.defaults.contextmenu}}"

; Choose the default context template

contexttemplate="{{data.nagvis_ini_php.defaults.contexttemplate}}"

; Raise frontend events for problematic objects also on page loading. Set to 1 to
; enable this feature

event_on_load="{{data.nagvis_ini_php.defaults.event_on_load}}"

; Repeat frontend events in the given interval. The interval is configured in seconds.

event_repeat_interval="{{data.nagvis_ini_php.defaults.event_repeat_interval}}"

; The time in seconds to repeat alerts for a problematic ojects for as configured in
; event_repeat_interval. This value defaults to -1, this leads to repeated events
; till the problematic state has been fixed.

event_repeat_duration="{{data.nagvis_ini_php.defaults.event_repeat_duration}}"

; Enable/Disable changing background color on state changes (Configured color is
; shown when summary state is PENDING, OK or UP)

eventbackground="{{data.nagvis_ini_php.defaults.eventbackground}}"

; Enable/Disable highlighting of the state changing object by adding a flashing
; border

eventhighlight="{{data.nagvis_ini_php.defaults.eventhighlight}}"

; The duration of the event highlight in milliseconds (10 seconds by default)

eventhighlightduration="{{data.nagvis_ini_php.defaults.eventhighlightduration}}"

; The interval of the event highlight in milliseconds (0.5 seconds by default)

eventhighlightinterval="{{data.nagvis_ini_php.defaults.eventhighlightinterval}}"

; Enable/Disable the eventlog in the new javascript frontend. The eventlog keeps
; track of important actions and information

eventlog="{{data.nagvis_ini_php.defaults.eventlog}}"

; Loglevel of the eventlog (available: debug, info, warning, critical)

eventloglevel="{{data.nagvis_ini_php.defaults.eventloglevel}}"

; Number of events kept in the scrollback

eventlogevents="{{data.nagvis_ini_php.defaults.eventlogevents}}"

; Height of the eventlog when visible in px

eventlogheight="{{data.nagvis_ini_php.defaults.eventlogheight}}"

; Hide/Show the eventlog on page load

eventloghidden="{{data.nagvis_ini_php.defaults.eventloghidden}}"

; Enable/Disable scrolling to the icon which changed the state when the icon is
; out of the visible scope

eventscroll="{{data.nagvis_ini_php.defaults.eventscroll}}"

; Enable/Disable sound signals on state changes

eventsound="{{data.nagvis_ini_php.defaults.eventsound}}"

; enable/disable header menu

headermenu="{{data.nagvis_ini_php.defaults.headermenu}}"

; header template

headertemplate="{{data.nagvis_ini_php.defaults.headertemplate}}"

; Enable/Diable the fading effect of the submenus in the header menu

headerfade="{{data.nagvis_ini_php.defaults.headerfade}}"

; enable/disable hover menu

hovermenu="{{data.nagvis_ini_php.defaults.hovermenu}}"

; hover template

hovertemplate="{{data.nagvis_ini_php.defaults.hovertemplate}}"

; hover menu open delay (seconds)

hoverdelay="{{data.nagvis_ini_php.defaults.hoverdelay}}"

; show children in hover menus

hoverchildsshow="{{data.nagvis_ini_php.defaults.hoverchildsshow}}"

; limit shown child objects to n

hoverchildslimit="{{data.nagvis_ini_php.defaults.hoverchildslimit}}"

; order method of children (desc: descending, asc: ascending)

hoverchildsorder="{{data.nagvis_ini_php.defaults.hoverchildsorder}}"

; sort method of children (s: state, a: alphabetical)

hoverchildssort="{{data.nagvis_ini_php.defaults.hoverchildssort}}"

; default icons

icons="{{data.nagvis_ini_php.defaults.icons}}"

; recognize only hard states (not soft)

onlyhardstates="{{data.nagvis_ini_php.defaults.onlyhardstates}}"

; recognize service states in host/hostgroup objects

recognizeservices="{{data.nagvis_ini_php.defaults.recognizeservices}}"

; show map in lists (dropdowns, index page, ...)

showinlists="{{data.nagvis_ini_php.defaults.showinlists}}"

; show map in multisite snapin

showinmultisite="{{data.nagvis_ini_php.defaults.showinmultisite}}"

; Name of the custom stylesheet to use on the maps (The file needs to be located
; in the share/nagvis/styles directory)

{% if data.nagvis_ini_php.defaults.get('stylesheet', None) %}
stylesheet="{{data.nagvis_ini_php.defaults.stylesheet}}"
{% endif %}

; target for the icon links

urltarget="{{data.nagvis_ini_php.defaults.urltarget}}"

; URL template for host object links

hosturl="{{data.nagvis_ini_php.defaults.hosturl}}"

; URL template for hostgroup object links

hostgroupurl="{{data.nagvis_ini_php.defaults.hostgroupurl}}"

; URL template for service object links

serviceurl="{{data.nagvis_ini_php.defaults.serviceurl}}"

; URL template for servicegroup object links

servicegroupurl="{{data.nagvis_ini_php.defaults.servicegroupurl}}"

; URL template for nested map links

mapurl="{{data.nagvis_ini_php.defaults.mapurl}}"

; Templates to be used for the different views.

view_template="{{data.nagvis_ini_php.defaults.view_template}}"

; Enable/disable object labels for all objects

label_show="{{data.nagvis_ini_php.defaults.label_show}}"

; Configure the colors used by weathermap lines

line_weather_colors="{{data.nagvis_ini_php.defaults.line_weather_colors}}"


; Options to configure the Overview page of NagVis
[index]
; Color of the overview background

backgroundcolor="{{data.nagvis_ini_php.index.backgroundcolor}}"

; Set number of map cells per row

cellsperrow="{{data.nagvis_ini_php.index.cellsperrow}}"

; enable/disable header menu

headermenu="{{data.nagvis_ini_php.index.headermenu}}"

; header template

headertemplate="{{data.nagvis_ini_php.index.headertemplate}}"

; Enable/Disable map listing

showmaps="{{data.nagvis_ini_php.index.showmaps}}"

; Enable/Disable geomap listing
;   Note: It is disabled here since it is unfinished yet and not for production
;         use in current 1.5 code.

showgeomap="{{data.nagvis_ini_php.index.showgeomap}}"

; Enable/Disable rotation listing

showrotations="{{data.nagvis_ini_php.index.showrotations}}"

; Enable/Disable map thumbnails

showmapthumbs="{{data.nagvis_ini_php.index.showmapthumbs}}"


; Options for the Automap
[automap]
; Default URL parameters for links to the automap

defaultparams="{{data.nagvis_ini_php.automap.defaultparams}}"

; Default root host (NagVis uses this if it can't detect it via backend)
; You can configure a hostname here or use "<<<monitoring>>>" as "virtual"
; node which shows the parent tree and all hosts which have no parents
; defined below the is node.

defaultroot="{{data.nagvis_ini_php.automap.defaultroot}}"

; Path to the graphviz binaries (dot,neato,...); Only needed if not in ENV PATH

graphvizpath="{{data.nagvis_ini_php.automap.graphvizpath}}"


; Options for the WUI
[wui]
; map lock time (minutes). When a user edits a map other users trying to edit
; the map are warned about this fact.

maplocktime="{{data.nagvis_ini_php.wui.maplocktime}}"

; Show/hide the grid

grid_show="{{data.nagvis_ini_php.wui.grid_show}}"

; The color of the grid lines

grid_color="{{data.nagvis_ini_php.wui.grid_color}}"

; The space between the single grid lines in pixels

grid_steps="{{data.nagvis_ini_php.wui.grid_steps}}"


; Options for the new Javascript worker
[worker]
; The interval in seconds in which the worker will check for objects which need
; to be updated

interval="{{data.nagvis_ini_php.worker.interval}}"

; The maximum number of parameters used in ajax http requests
; Some intrusion detection/prevention systems have a problem with
; too many parameters in the url. Give 0 for no limit.

requestmaxparams="{{data.nagvis_ini_php.worker.requestmaxparams}}"

; The maximum length of http request urls during ajax http requests
; Some intrusion detection/prevention systems have a problem with
; queries being too long

requestmaxlength="{{data.nagvis_ini_php.worker.requestmaxlength}}"

; The retention time of the states in the frontend in seconds. The state
; information will be refreshed after this time

updateobjectstates="{{data.nagvis_ini_php.worker.updateobjectstates}}"


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

down="{{data.nagvis_ini_php.states.down}}"


down_ack="{{data.nagvis_ini_php.states.down_ack}}"


down_downtime="{{data.nagvis_ini_php.states.down_downtime}}"


unreachable="{{data.nagvis_ini_php.states.unreachable}}"


unreachable_ack="{{data.nagvis_ini_php.states.unreachable_ack}}"


unreachable_downtime="{{data.nagvis_ini_php.states.unreachable_downtime}}"


critical="{{data.nagvis_ini_php.states.critical}}"


critical_ack="{{data.nagvis_ini_php.states.critical_ack}}"


critical_downtime="{{data.nagvis_ini_php.states.critical_downtime}}"


warning="{{data.nagvis_ini_php.states.warning}}"


warning_ack="{{data.nagvis_ini_php.states.warning_ack}}"


warning_downtime="{{data.nagvis_ini_php.states.warning_downtime}}"


unknown="{{data.nagvis_ini_php.states.unknown}}"


unknown_ack="{{data.nagvis_ini_php.states.unknown_ack}}"


unknown_downtime="{{data.nagvis_ini_php.states.unknown_downtime}}"


error="{{data.nagvis_ini_php.states.error}}"


error_ack="{{data.nagvis_ini_php.states.error_ack}}"


error_downtime="{{data.nagvis_ini_php.states.error_downtime}}"


up="{{data.nagvis_ini_php.states.up}}"


ok="{{data.nagvis_ini_php.states.ok}}"


unchecked="{{data.nagvis_ini_php.states.unchecked}}"


pending="{{data.nagvis_ini_php.states.pending}}"

;
; Colors of the different states. The colors are used in lines and hover menus
; and for example in the frontend highlight and background event handler
;

unreachable_bgcolor="{{data.nagvis_ini_php.states.unreachable_bgcolor}}"


unreachable_color="{{data.nagvis_ini_php.states.unreachable_color}}"

{% if data.nagvis_ini_php.states.get('unreachable_ack_bgcolor', None) %}
unreachable_ack_bgcolor="{{data.nagvis_ini_php.states.unreachable_ack_bgcolor}}"
{% endif %}

{% if data.nagvis_ini_php.states.get('unreachable_downtime_bgcolor', None) %}
unreachable_downtime_bgcolor="{{data.nagvis_ini_php.states.unreachable_downtime_bgcolor}}"
{% endif %}

down_bgcolor="{{data.nagvis_ini_php.states.down_bgcolor}}"


down_color="{{data.nagvis_ini_php.states.down_color}}"


{% if data.nagvis_ini_php.states.get('down_ack_bgcolor', None) %}
down_ack_bgcolor="{{data.nagvis_ini_php.states.down_ack_bgcolor}}"
{% endif %}

{% if data.nagvis_ini_php.states.get('down_downtime_bgcolor', None) %}
down_downtime_bgcolor="{{data.nagvis_ini_php.states.down_downtime_bgcolor}}"
{% endif %}

critical_bgcolor="{{data.nagvis_ini_php.states.critical_bgcolor}}"


critical_color="{{data.nagvis_ini_php.states.critical_color}}"



{% if data.nagvis_ini_php.states.get('critical_ack_bgcolor', None) %}
critical_ack_bgcolor="{{data.nagvis_ini_php.states.critical_ack_bgcolor}}"
{% endif %}

{% if data.nagvis_ini_php.states.get('critical_downtime_bgcolor', None) %}
critical_downtime_bgcolor="{{data.nagvis_ini_php.states.critical_downtime_bgcolor}}"
{% endif %}

warning_bgcolor="{{data.nagvis_ini_php.states.warning_bgcolor}}"


warning_color="{{data.nagvis_ini_php.states.warning_color}}"


{% if data.nagvis_ini_php.states.get('warning_ack_bgcolor', None) %}
warning_ack_bgcolor="{{data.nagvis_ini_php.states.warning_ack_bgcolor}}"
{% endif %}

{% if data.nagvis_ini_php.states.get('warning_downtime_bgolor', None) %}
warning_downtime_bgcolor="{{data.nagvis_ini_php.states.warning_downtime_bgcolor}}"
{% endif %}


unknown_bgcolor="{{data.nagvis_ini_php.states.unknown_bgcolor}}"


unknown_color="{{data.nagvis_ini_php.states.unknown_color}}"


{% if data.nagvis_ini_php.states.get('unknown_ack_bgolor', None) %}
unknown_ack_bgcolor="{{data.nagvis_ini_php.states.unknown_ack_bgcolor}}"
{% endif %}

{% if data.nagvis_ini_php.states.get('unknown_downtime_bgolor', None) %}
unknown_downtime_bgcolor="{{data.nagvis_ini_php.states.unknown_downtime_bgcolor}}"
{% endif %}


error_bgcolor="{{data.nagvis_ini_php.states.error_bgcolor}}"


error_color="{{data.nagvis_ini_php.states.error_color}}"


up_bgcolor="{{data.nagvis_ini_php.states.up_bgcolor}}"


up_color="{{data.nagvis_ini_php.states.up_color}}"


ok_bgcolor="{{data.nagvis_ini_php.states.ok_bgcolor}}"


ok_color="{{data.nagvis_ini_php.states.ok_color}}"


unchecked_bgcolor="{{data.nagvis_ini_php.states.unchecked_bgcolor}}"


unchecked_color="{{data.nagvis_ini_php.states.unchecked_color}}"


pending_bgcolor="{{data.nagvis_ini_php.states.pending_bgcolor}}"


pending_color="{{data.nagvis_ini_php.states.pending_color}}"

;
; Sound of the different states to be used by the sound eventhandler in the
; frontend. The sounds are only being fired when changing to some
; worse state.
;

unreachable_sound="{{data.nagvis_ini_php.states.unreachable_sound}}"


down_sound="{{data.nagvis_ini_php.states.down_sound}}"


critical_sound="{{data.nagvis_ini_php.states.critical_sound}}"


warning_sound="{{data.nagvis_ini_php.states.warning_sound}}"

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
