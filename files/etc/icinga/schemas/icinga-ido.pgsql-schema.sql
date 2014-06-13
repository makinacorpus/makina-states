{% set data = salt['mc_utils.json_load'](data) %}
-- MANAGED VIA SALT -- DO NOT EDIT
-- from /usr/share/doc/icinga-idoutils/examples/pgsql/pgsql.sql
-- --------------------------------------------------------
-- pgsql.sql
-- DB definition for Postgresql
--
-- Copyright (c) 2009-2013 Icinga Development Team (http://www.icinga.org)
--
-- initial version: 2009-05-13 Markus Manzke
-- current version: 2012-04-19 Michael Friedrich <michael.friedrich@univie.ac.at>
--
-- --------------------------------------------------------

--
-- Functions
--

CREATE OR REPLACE FUNCTION from_unixtime(bigint) RETURNS timestamp with time zone AS '
         SELECT to_timestamp($1) AS result
' LANGUAGE sql;

CREATE OR REPLACE FUNCTION unix_timestamp(timestamp with time zone) RETURNS bigint AS '
        SELECT EXTRACT(EPOCH FROM $1)::bigint AS result;
' LANGUAGE sql;


-- -----------------------------------------
-- set dbversion
-- -----------------------------------------

CREATE OR REPLACE FUNCTION updatedbversion(version_i TEXT) RETURNS void AS $$
BEGIN
        IF EXISTS( SELECT * FROM {{data.modules.ido2db.database.prefix}}dbversion WHERE name='idoutils')
        THEN
                UPDATE {{data.modules.ido2db.database.prefix}}dbversion
                SET version=version_i, modify_time=NOW()
		WHERE name='idoutils';
        ELSE
                INSERT INTO {{data.modules.ido2db.database.prefix}}dbversion (dbversion_id, name, version, create_time, modify_time) VALUES ('1', 'idoutils', version_i, NOW(), NOW());
        END IF;

        RETURN;
END;
$$ LANGUAGE plpgsql;
-- HINT: su - postgres; createlang plpgsql icinga;



--
-- Database: icinga
--

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}acknowledgements
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}acknowledgements (
  acknowledgement_id bigserial,
  instance_id bigint default 0,
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  entry_time_usec INTEGER  default 0,
  acknowledgement_type INTEGER  default 0,
  object_id bigint default 0,
  state INTEGER  default 0,
  author_name TEXT  default '',
  comment_data TEXT  default '',
  is_sticky INTEGER  default 0,
  persistent_comment INTEGER  default 0,
  notify_contacts INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  CONSTRAINT PK_acknowledgement_id PRIMARY KEY (acknowledgement_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}commands
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}commands (
  command_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  object_id bigint default 0,
  command_line TEXT  default '',
  CONSTRAINT PK_command_id PRIMARY KEY (command_id) ,
  CONSTRAINT UQ_commands UNIQUE (instance_id,object_id,config_type)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}commenthistory
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}commenthistory (
  commenthistory_id bigserial,
  instance_id bigint default 0,
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  entry_time_usec INTEGER  default 0,
  comment_type INTEGER  default 0,
  entry_type INTEGER  default 0,
  object_id bigint default 0,
  comment_time timestamp with time zone default '1970-01-01 00:00:00',
  internal_comment_id bigint default 0,
  author_name TEXT  default '',
  comment_data TEXT  default '',
  is_persistent INTEGER  default 0,
  comment_source INTEGER  default 0,
  expires INTEGER  default 0,
  expiration_time timestamp with time zone default '1970-01-01 00:00:00',
  deletion_time timestamp with time zone default '1970-01-01 00:00:00',
  deletion_time_usec INTEGER  default 0,
  CONSTRAINT PK_commenthistory_id PRIMARY KEY (commenthistory_id) ,
  CONSTRAINT UQ_commenthistory UNIQUE (instance_id,object_id,comment_time,internal_comment_id)
);

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}comments
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}comments (
  comment_id bigserial,
  instance_id bigint default 0,
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  entry_time_usec INTEGER  default 0,
  comment_type INTEGER  default 0,
  entry_type INTEGER  default 0,
  object_id bigint default 0,
  comment_time timestamp with time zone default '1970-01-01 00:00:00',
  internal_comment_id bigint default 0,
  author_name TEXT  default '',
  comment_data TEXT  default '',
  is_persistent INTEGER  default 0,
  comment_source INTEGER  default 0,
  expires INTEGER  default 0,
  expiration_time timestamp with time zone default '1970-01-01 00:00:00',
  CONSTRAINT PK_comment_id PRIMARY KEY (comment_id) ,
  CONSTRAINT UQ_comments UNIQUE (instance_id,object_id,comment_time,internal_comment_id)
)  ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}configfiles
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}configfiles (
  configfile_id bigserial,
  instance_id bigint default 0,
  configfile_type INTEGER  default 0,
  configfile_path TEXT  default '',
  CONSTRAINT PK_configfile_id PRIMARY KEY (configfile_id) ,
  CONSTRAINT UQ_configfiles UNIQUE (instance_id,configfile_type,configfile_path)
);

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}configfilevariables
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}configfilevariables (
  configfilevariable_id bigserial,
  instance_id bigint default 0,
  configfile_id bigint default 0,
  varname TEXT  default '',
  varvalue TEXT  default '',
  CONSTRAINT PK_configfilevariable_id PRIMARY KEY (configfilevariable_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}conninfo
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}conninfo (
  conninfo_id bigserial,
  instance_id bigint default 0,
  agent_name TEXT  default '',
  agent_version TEXT  default '',
  disposition TEXT  default '',
  connect_source TEXT  default '',
  connect_type TEXT  default '',
  connect_time timestamp with time zone default '1970-01-01 00:00:00',
  disconnect_time timestamp with time zone default '1970-01-01 00:00:00',
  last_checkin_time timestamp with time zone default '1970-01-01 00:00:00',
  data_start_time timestamp with time zone default '1970-01-01 00:00:00',
  data_end_time timestamp with time zone default '1970-01-01 00:00:00',
  bytes_processed bigint  default 0,
  lines_processed bigint  default 0,
  entries_processed bigint  default 0,
  CONSTRAINT PK_conninfo_id PRIMARY KEY (conninfo_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactgroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contactgroups (
  contactgroup_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  contactgroup_object_id bigint default 0,
  alias TEXT  default '',
  CONSTRAINT PK_contactgroup_id PRIMARY KEY (contactgroup_id) ,
  CONSTRAINT UQ_contactgroups UNIQUE (instance_id,config_type,contactgroup_object_id)
);

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactgroup_members
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contactgroup_members (
  contactgroup_member_id bigserial,
  instance_id bigint default 0,
  contactgroup_id bigint default 0,
  contact_object_id bigint default 0,
  CONSTRAINT PK_contactgroup_member_id PRIMARY KEY (contactgroup_member_id)
);

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactnotificationmethods
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contactnotificationmethods (
  contactnotificationmethod_id bigserial,
  instance_id bigint default 0,
  contactnotification_id bigint default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  command_object_id bigint default 0,
  command_args TEXT  default '',
  CONSTRAINT PK_contactnotificationmethod_id PRIMARY KEY (contactnotificationmethod_id) ,
  CONSTRAINT UQ_contactnotificationmethods UNIQUE (instance_id,contactnotification_id,start_time,start_time_usec)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactnotifications
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contactnotifications (
  contactnotification_id bigserial,
  instance_id bigint default 0,
  notification_id bigint default 0,
  contact_object_id bigint default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  CONSTRAINT PK_contactnotification_id PRIMARY KEY (contactnotification_id) ,
  CONSTRAINT UQ_contactnotifications UNIQUE (instance_id,contact_object_id,start_time,start_time_usec)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contacts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contacts (
  contact_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  contact_object_id bigint default 0,
  alias TEXT  default '',
  email_address TEXT  default '',
  pager_address TEXT  default '',
  host_timeperiod_object_id bigint default 0,
  service_timeperiod_object_id bigint default 0,
  host_notifications_enabled INTEGER  default 0,
  service_notifications_enabled INTEGER  default 0,
  can_submit_commands INTEGER  default 0,
  notify_service_recovery INTEGER  default 0,
  notify_service_warning INTEGER  default 0,
  notify_service_unknown INTEGER  default 0,
  notify_service_critical INTEGER  default 0,
  notify_service_flapping INTEGER  default 0,
  notify_service_downtime INTEGER  default 0,
  notify_host_recovery INTEGER  default 0,
  notify_host_down INTEGER  default 0,
  notify_host_unreachable INTEGER  default 0,
  notify_host_flapping INTEGER  default 0,
  notify_host_downtime INTEGER  default 0,
  CONSTRAINT PK_contact_id PRIMARY KEY (contact_id) ,
  CONSTRAINT UQ_contacts UNIQUE (instance_id,config_type,contact_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactstatus
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contactstatus (
  contactstatus_id bigserial,
  instance_id bigint default 0,
  contact_object_id bigint default 0,
  status_update_time timestamp with time zone default '1970-01-01 00:00:00',
  host_notifications_enabled INTEGER  default 0,
  service_notifications_enabled INTEGER  default 0,
  last_host_notification timestamp with time zone default '1970-01-01 00:00:00',
  last_service_notification timestamp with time zone default '1970-01-01 00:00:00',
  modified_attributes INTEGER  default 0,
  modified_host_attributes INTEGER  default 0,
  modified_service_attributes INTEGER  default 0,
  CONSTRAINT PK_contactstatus_id PRIMARY KEY (contactstatus_id) ,
  CONSTRAINT UQ_contactstatus UNIQUE (contact_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contact_addresses
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contact_addresses (
  contact_address_id bigserial,
  instance_id bigint default 0,
  contact_id bigint default 0,
  address_number INTEGER  default 0,
  address TEXT  default '',
  CONSTRAINT PK_contact_address_id PRIMARY KEY (contact_address_id) ,
  CONSTRAINT UQ_contact_addresses UNIQUE (contact_id,address_number)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contact_notificationcommands
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}contact_notificationcommands (
  contact_notificationcommand_id bigserial,
  instance_id bigint default 0,
  contact_id bigint default 0,
  notification_type INTEGER  default 0,
  command_object_id bigint default 0,
  command_args TEXT  default '',
  CONSTRAINT PK_contact_notificationcommand_id PRIMARY KEY (contact_notificationcommand_id) ,
  CONSTRAINT UQ_contact_notificationcommands UNIQUE (contact_id,notification_type,command_object_id,command_args)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}customvariables
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}customvariables (
  customvariable_id bigserial,
  instance_id bigint default 0,
  object_id bigint default 0,
  config_type INTEGER  default 0,
  has_been_modified INTEGER  default 0,
  varname TEXT  default '',
  varvalue TEXT  default '',
  CONSTRAINT PK_customvariable_id PRIMARY KEY (customvariable_id) ,
  CONSTRAINT UQ_customvariables UNIQUE (object_id,config_type,varname)
) ;
CREATE INDEX {{data.modules.ido2db.database.prefix}}customvariables_i ON {{data.modules.ido2db.database.prefix}}customvariables(varname);

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}customvariablestatus
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}customvariablestatus (
  customvariablestatus_id bigserial,
  instance_id bigint default 0,
  object_id bigint default 0,
  status_update_time timestamp with time zone default '1970-01-01 00:00:00',
  has_been_modified INTEGER  default 0,
  varname TEXT  default '',
  varvalue TEXT  default '',
  CONSTRAINT PK_customvariablestatus_id PRIMARY KEY (customvariablestatus_id) ,
  CONSTRAINT UQ_customvariablestatus UNIQUE (object_id,varname)
) ;
CREATE INDEX {{data.modules.ido2db.database.prefix}}customvariablestatus_i ON {{data.modules.ido2db.database.prefix}}customvariablestatus(varname);


-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}dbversion
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}dbversion (
  dbversion_id bigserial,
  name TEXT  default '',
  version TEXT  default '',
  create_time timestamp with time zone default '1970-01-01 00:00:00',
  modify_time timestamp with time zone default '1970-01-01 00:00:00',
  CONSTRAINT PK_dbversion_id PRIMARY KEY (dbversion_id) ,
  CONSTRAINT UQ_dbversion UNIQUE (name)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}downtimehistory
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}downtimehistory (
  downtimehistory_id bigserial,
  instance_id bigint default 0,
  downtime_type INTEGER  default 0,
  object_id bigint default 0,
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  author_name TEXT  default '',
  comment_data TEXT  default '',
  internal_downtime_id bigint default 0,
  triggered_by_id bigint default 0,
  is_fixed INTEGER  default 0,
  duration BIGINT  default 0,
  scheduled_start_time timestamp with time zone default '1970-01-01 00:00:00',
  scheduled_end_time timestamp with time zone default '1970-01-01 00:00:00',
  was_started INTEGER  default 0,
  actual_start_time timestamp with time zone default '1970-01-01 00:00:00',
  actual_start_time_usec INTEGER  default 0,
  actual_end_time timestamp with time zone default '1970-01-01 00:00:00',
  actual_end_time_usec INTEGER  default 0,
  was_cancelled INTEGER  default 0,
  is_in_effect INTEGER  default 0,
  trigger_time timestamp with time zone default '1970-01-01 00:00:00',
  CONSTRAINT PK_downtimehistory_id PRIMARY KEY (downtimehistory_id) ,
  CONSTRAINT UQ_downtimehistory UNIQUE (instance_id,object_id,entry_time,internal_downtime_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}eventhandlers
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}eventhandlers (
  eventhandler_id bigserial,
  instance_id bigint default 0,
  eventhandler_type INTEGER  default 0,
  object_id bigint default 0,
  state INTEGER  default 0,
  state_type INTEGER  default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  command_object_id bigint default 0,
  command_args TEXT  default '',
  command_line TEXT  default '',
  timeout INTEGER  default 0,
  early_timeout INTEGER  default 0,
  execution_time double precision  default 0,
  return_code INTEGER  default 0,
  output TEXT  default '',
  long_output TEXT  default '',
  CONSTRAINT PK_eventhandler_id PRIMARY KEY (eventhandler_id) ,
  CONSTRAINT UQ_eventhandlers UNIQUE (instance_id,object_id,start_time,start_time_usec)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}externalcommands
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}externalcommands (
  externalcommand_id bigserial,
  instance_id bigint default 0,
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  command_type INTEGER  default 0,
  command_name TEXT  default '',
  command_args TEXT  default '',
  CONSTRAINT PK_externalcommand_id PRIMARY KEY (externalcommand_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}flappinghistory
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}flappinghistory (
  flappinghistory_id bigserial,
  instance_id bigint default 0,
  event_time timestamp with time zone default '1970-01-01 00:00:00',
  event_time_usec INTEGER  default 0,
  event_type INTEGER  default 0,
  reason_type INTEGER  default 0,
  flapping_type INTEGER  default 0,
  object_id bigint default 0,
  percent_state_change double precision  default 0,
  low_threshold double precision  default 0,
  high_threshold double precision  default 0,
  comment_time timestamp with time zone default '1970-01-01 00:00:00',
  internal_comment_id bigint default 0,
  CONSTRAINT PK_flappinghistory_id PRIMARY KEY (flappinghistory_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostchecks
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostchecks (
  hostcheck_id bigserial,
  instance_id bigint default 0,
  host_object_id bigint default 0,
  check_type INTEGER  default 0,
  is_raw_check INTEGER  default 0,
  current_check_attempt INTEGER  default 0,
  max_check_attempts INTEGER  default 0,
  state INTEGER  default 0,
  state_type INTEGER  default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  command_object_id bigint default 0,
  command_args TEXT  default '',
  command_line TEXT  default '',
  timeout INTEGER  default 0,
  early_timeout INTEGER  default 0,
  execution_time double precision  default 0,
  latency double precision  default 0,
  return_code INTEGER  default 0,
  output TEXT  default '',
  long_output TEXT  default '',
  perfdata TEXT  default '',
  CONSTRAINT PK_hostcheck_id PRIMARY KEY (hostcheck_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostdependencies
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostdependencies (
  hostdependency_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  host_object_id bigint default 0,
  dependent_host_object_id bigint default 0,
  dependency_type INTEGER  default 0,
  inherits_parent INTEGER  default 0,
  timeperiod_object_id bigint default 0,
  fail_on_up INTEGER  default 0,
  fail_on_down INTEGER  default 0,
  fail_on_unreachable INTEGER  default 0,
  CONSTRAINT PK_hostdependency_id PRIMARY KEY (hostdependency_id) ,
  CONSTRAINT UQ_hostdependencies UNIQUE (instance_id,config_type,host_object_id,dependent_host_object_id,dependency_type,inherits_parent,fail_on_up,fail_on_down,fail_on_unreachable)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostescalations
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostescalations (
  hostescalation_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  host_object_id bigint default 0,
  timeperiod_object_id bigint default 0,
  first_notification INTEGER  default 0,
  last_notification INTEGER  default 0,
  notification_interval double precision  default 0,
  escalate_on_recovery INTEGER  default 0,
  escalate_on_down INTEGER  default 0,
  escalate_on_unreachable INTEGER  default 0,
  CONSTRAINT PK_hostescalation_id PRIMARY KEY (hostescalation_id) ,
  CONSTRAINT UQ_hostescalations UNIQUE (instance_id,config_type,host_object_id,timeperiod_object_id,first_notification,last_notification)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostescalation_contactgroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostescalation_contactgroups (
  hostescalation_contactgroup_id bigserial,
  instance_id bigint default 0,
  hostescalation_id bigint default 0,
  contactgroup_object_id bigint default 0,
  CONSTRAINT PK_hostescalation_contactgroup_id PRIMARY KEY (hostescalation_contactgroup_id) ,
  CONSTRAINT UQ_hostescalation_contactgroups UNIQUE (hostescalation_id,contactgroup_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostescalation_contacts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostescalation_contacts (
  hostescalation_contact_id bigserial,
  instance_id bigint default 0,
  hostescalation_id bigint default 0,
  contact_object_id bigint default 0,
  CONSTRAINT PK_hostescalation_contact_id PRIMARY KEY (hostescalation_contact_id) ,
  CONSTRAINT UQ_hostescalation_contacts UNIQUE (instance_id,hostescalation_id,contact_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostgroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostgroups (
  hostgroup_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  hostgroup_object_id bigint default 0,
  alias TEXT  default '',
  CONSTRAINT PK_hostgroup_id PRIMARY KEY (hostgroup_id) ,
  CONSTRAINT UQ_hostgroups UNIQUE (instance_id,hostgroup_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostgroup_members
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hostgroup_members (
  hostgroup_member_id bigserial,
  instance_id bigint default 0,
  hostgroup_id bigint default 0,
  host_object_id bigint default 0,
  CONSTRAINT PK_hostgroup_member_id PRIMARY KEY (hostgroup_member_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hosts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hosts (
  host_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  host_object_id bigint default 0,
  alias TEXT  default '',
  display_name TEXT  default '',
  address TEXT  default '',
  address6 TEXT  default '',
  check_command_object_id bigint default 0,
  check_command_args TEXT  default '',
  eventhandler_command_object_id bigint default 0,
  eventhandler_command_args TEXT  default '',
  notification_timeperiod_object_id bigint default 0,
  check_timeperiod_object_id bigint default 0,
  failure_prediction_options TEXT  default '',
  check_interval double precision  default 0,
  retry_interval double precision  default 0,
  max_check_attempts INTEGER  default 0,
  first_notification_delay double precision  default 0,
  notification_interval double precision  default 0,
  notify_on_down INTEGER  default 0,
  notify_on_unreachable INTEGER  default 0,
  notify_on_recovery INTEGER  default 0,
  notify_on_flapping INTEGER  default 0,
  notify_on_downtime INTEGER  default 0,
  stalk_on_up INTEGER  default 0,
  stalk_on_down INTEGER  default 0,
  stalk_on_unreachable INTEGER  default 0,
  flap_detection_enabled INTEGER  default 0,
  flap_detection_on_up INTEGER  default 0,
  flap_detection_on_down INTEGER  default 0,
  flap_detection_on_unreachable INTEGER  default 0,
  low_flap_threshold double precision  default 0,
  high_flap_threshold double precision  default 0,
  process_performance_data INTEGER  default 0,
  freshness_checks_enabled INTEGER  default 0,
  freshness_threshold INTEGER  default 0,
  passive_checks_enabled INTEGER  default 0,
  event_handler_enabled INTEGER  default 0,
  active_checks_enabled INTEGER  default 0,
  retain_status_information INTEGER  default 0,
  retain_nonstatus_information INTEGER  default 0,
  notifications_enabled INTEGER  default 0,
  obsess_over_host INTEGER  default 0,
  failure_prediction_enabled INTEGER  default 0,
  notes TEXT  default '',
  notes_url TEXT  default '',
  action_url TEXT  default '',
  icon_image TEXT  default '',
  icon_image_alt TEXT  default '',
  vrml_image TEXT  default '',
  statusmap_image TEXT  default '',
  have_2d_coords INTEGER  default 0,
  x_2d INTEGER  default 0,
  y_2d INTEGER  default 0,
  have_3d_coords INTEGER  default 0,
  x_3d double precision  default 0,
  y_3d double precision  default 0,
  z_3d double precision  default 0,
  CONSTRAINT PK_host_id PRIMARY KEY (host_id) ,
  CONSTRAINT UQ_hosts UNIQUE (instance_id,config_type,host_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hoststatus
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}hoststatus (
  hoststatus_id bigserial,
  instance_id bigint default 0,
  host_object_id bigint default 0,
  status_update_time timestamp with time zone default '1970-01-01 00:00:00',
  output TEXT  default '',
  long_output TEXT  default '',
  perfdata TEXT  default '',
  check_source TEXT  default '',
  current_state INTEGER  default 0,
  has_been_checked INTEGER  default 0,
  should_be_scheduled INTEGER  default 0,
  current_check_attempt INTEGER  default 0,
  max_check_attempts INTEGER  default 0,
  last_check timestamp with time zone default '1970-01-01 00:00:00',
  next_check timestamp with time zone default '1970-01-01 00:00:00',
  check_type INTEGER  default 0,
  last_state_change timestamp with time zone default '1970-01-01 00:00:00',
  last_hard_state_change timestamp with time zone default '1970-01-01 00:00:00',
  last_hard_state INTEGER  default 0,
  last_time_up timestamp with time zone default '1970-01-01 00:00:00',
  last_time_down timestamp with time zone default '1970-01-01 00:00:00',
  last_time_unreachable timestamp with time zone default '1970-01-01 00:00:00',
  state_type INTEGER  default 0,
  last_notification timestamp with time zone default '1970-01-01 00:00:00',
  next_notification timestamp with time zone default '1970-01-01 00:00:00',
  no_more_notifications INTEGER  default 0,
  notifications_enabled INTEGER  default 0,
  problem_has_been_acknowledged INTEGER  default 0,
  acknowledgement_type INTEGER  default 0,
  current_notification_number INTEGER  default 0,
  passive_checks_enabled INTEGER  default 0,
  active_checks_enabled INTEGER  default 0,
  event_handler_enabled INTEGER  default 0,
  flap_detection_enabled INTEGER  default 0,
  is_flapping INTEGER  default 0,
  percent_state_change double precision  default 0,
  latency double precision  default 0,
  execution_time double precision  default 0,
  scheduled_downtime_depth INTEGER  default 0,
  failure_prediction_enabled INTEGER  default 0,
  process_performance_data INTEGER  default 0,
  obsess_over_host INTEGER  default 0,
  modified_host_attributes INTEGER  default 0,
  event_handler TEXT  default '',
  check_command TEXT  default '',
  normal_check_interval double precision  default 0,
  retry_check_interval double precision  default 0,
  check_timeperiod_object_id bigint default 0,
  CONSTRAINT PK_hoststatus_id PRIMARY KEY (hoststatus_id) ,
  CONSTRAINT UQ_hoststatus UNIQUE (host_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}host_contactgroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}host_contactgroups (
  host_contactgroup_id bigserial,
  instance_id bigint default 0,
  host_id bigint default 0,
  contactgroup_object_id bigint default 0,
  CONSTRAINT PK_host_contactgroup_id PRIMARY KEY (host_contactgroup_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}host_contacts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}host_contacts (
  host_contact_id bigserial,
  instance_id bigint default 0,
  host_id bigint default 0,
  contact_object_id bigint default 0,
  CONSTRAINT PK_host_contact_id PRIMARY KEY (host_contact_id) 
)  ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}host_parenthosts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}host_parenthosts (
  host_parenthost_id bigserial,
  instance_id bigint default 0,
  host_id bigint default 0,
  parent_host_object_id bigint default 0,
  CONSTRAINT PK_host_parenthost_id PRIMARY KEY (host_parenthost_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}instances
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}instances (
  instance_id bigserial,
  instance_name TEXT  default '',
  instance_description TEXT  default '',
  CONSTRAINT PK_instance_id PRIMARY KEY (instance_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}logentries
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}logentries (
  logentry_id bigserial,
  instance_id bigint default 0,
  logentry_time timestamp with time zone default '1970-01-01 00:00:00',
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  entry_time_usec INTEGER  default 0,
  logentry_type INTEGER  default 0,
  logentry_data TEXT  default '',
  realtime_data INTEGER  default 0,
  inferred_data_extracted INTEGER  default 0,
  object_id bigint default NULL,
  CONSTRAINT PK_logentry_id PRIMARY KEY (logentry_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}notifications
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}notifications (
  notification_id bigserial,
  instance_id bigint default 0,
  notification_type INTEGER  default 0,
  notification_reason INTEGER  default 0,
  object_id bigint default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  state INTEGER  default 0,
  output TEXT  default '',
  long_output TEXT  default '',
  escalated INTEGER  default 0,
  contacts_notified INTEGER  default 0,
  CONSTRAINT PK_notification_id PRIMARY KEY (notification_id) ,
  CONSTRAINT UQ_notifications UNIQUE (instance_id,object_id,start_time,start_time_usec)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}objects
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}objects (
  object_id bigserial,
  instance_id bigint default 0,
  objecttype_id bigint default 0,
  name1 TEXT,
  name2 TEXT,
  is_active INTEGER  default 0,
  CONSTRAINT PK_object_id PRIMARY KEY (object_id) 
--  UNIQUE (objecttype_id,name1,name2)
) ;
CREATE INDEX {{data.modules.ido2db.database.prefix}}objects_i ON {{data.modules.ido2db.database.prefix}}objects(objecttype_id,name1,name2);

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}processevents
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}processevents (
  processevent_id bigserial,
  instance_id bigint default 0,
  event_type INTEGER  default 0,
  event_time timestamp with time zone default '1970-01-01 00:00:00',
  event_time_usec INTEGER  default 0,
  process_id bigint default 0,
  program_name TEXT  default '',
  program_version TEXT  default '',
  program_date TEXT  default '',
  CONSTRAINT PK_processevent_id PRIMARY KEY (processevent_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}programstatus
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}programstatus (
  programstatus_id bigserial,
  instance_id bigint default 0,
  status_update_time timestamp with time zone default '1970-01-01 00:00:00',
  program_start_time timestamp with time zone default '1970-01-01 00:00:00',
  program_end_time timestamp with time zone default '1970-01-01 00:00:00',
  is_currently_running INTEGER  default 0,
  process_id bigint default 0,
  daemon_mode INTEGER  default 0,
  last_command_check timestamp with time zone default '1970-01-01 00:00:00',
  last_log_rotation timestamp with time zone default '1970-01-01 00:00:00',
  notifications_enabled INTEGER  default 0,
  disable_notif_expire_time timestamp with time zone default '1970-01-01 00:00:00',
  active_service_checks_enabled INTEGER  default 0,
  passive_service_checks_enabled INTEGER  default 0,
  active_host_checks_enabled INTEGER  default 0,
  passive_host_checks_enabled INTEGER  default 0,
  event_handlers_enabled INTEGER  default 0,
  flap_detection_enabled INTEGER  default 0,
  failure_prediction_enabled INTEGER  default 0,
  process_performance_data INTEGER  default 0,
  obsess_over_hosts INTEGER  default 0,
  obsess_over_services INTEGER  default 0,
  modified_host_attributes INTEGER  default 0,
  modified_service_attributes INTEGER  default 0,
  global_host_event_handler TEXT  default '',
  global_service_event_handler TEXT  default '',
  CONSTRAINT PK_programstatus_id PRIMARY KEY (programstatus_id) ,
  CONSTRAINT UQ_programstatus UNIQUE (instance_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}runtimevariables
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}runtimevariables (
  runtimevariable_id bigserial,
  instance_id bigint default 0,
  varname TEXT  default '',
  varvalue TEXT  default '',
  CONSTRAINT PK_runtimevariable_id PRIMARY KEY (runtimevariable_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}scheduleddowntime
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}scheduleddowntime (
  scheduleddowntime_id bigserial,
  instance_id bigint default 0,
  downtime_type INTEGER  default 0,
  object_id bigint default 0,
  entry_time timestamp with time zone default '1970-01-01 00:00:00',
  author_name TEXT  default '',
  comment_data TEXT  default '',
  internal_downtime_id bigint default 0,
  triggered_by_id bigint default 0,
  is_fixed INTEGER  default 0,
  duration BIGINT  default 0,
  scheduled_start_time timestamp with time zone default '1970-01-01 00:00:00',
  scheduled_end_time timestamp with time zone default '1970-01-01 00:00:00',
  was_started INTEGER  default 0,
  actual_start_time timestamp with time zone default '1970-01-01 00:00:00',
  actual_start_time_usec INTEGER  default 0,
  is_in_effect INTEGER  default 0,
  trigger_time timestamp with time zone default '1970-01-01 00:00:00',
  CONSTRAINT PK_scheduleddowntime_id PRIMARY KEY (scheduleddowntime_id) ,
  CONSTRAINT UQ_scheduleddowntime UNIQUE (instance_id,object_id,entry_time,internal_downtime_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicechecks
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}servicechecks (
  servicecheck_id bigserial,
  instance_id bigint default 0,
  service_object_id bigint default 0,
  check_type INTEGER  default 0,
  current_check_attempt INTEGER  default 0,
  max_check_attempts INTEGER  default 0,
  state INTEGER  default 0,
  state_type INTEGER  default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  command_object_id bigint default 0,
  command_args TEXT  default '',
  command_line TEXT  default '',
  timeout INTEGER  default 0,
  early_timeout INTEGER  default 0,
  execution_time double precision  default 0,
  latency double precision  default 0,
  return_code INTEGER  default 0,
  output TEXT  default '',
  long_output TEXT  default '',
  perfdata TEXT  default '',
  CONSTRAINT PK_servicecheck_id PRIMARY KEY (servicecheck_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicedependencies
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}servicedependencies (
  servicedependency_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  service_object_id bigint default 0,
  dependent_service_object_id bigint default 0,
  dependency_type INTEGER  default 0,
  inherits_parent INTEGER  default 0,
  timeperiod_object_id bigint default 0,
  fail_on_ok INTEGER  default 0,
  fail_on_warning INTEGER  default 0,
  fail_on_unknown INTEGER  default 0,
  fail_on_critical INTEGER  default 0,
  CONSTRAINT PK_servicedependency_id PRIMARY KEY (servicedependency_id) ,
  CONSTRAINT UQ_servicedependencies UNIQUE (instance_id,config_type,service_object_id,dependent_service_object_id,dependency_type,inherits_parent,fail_on_ok,fail_on_warning,fail_on_unknown,fail_on_critical)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}serviceescalations
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}serviceescalations (
  serviceescalation_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  service_object_id bigint default 0,
  timeperiod_object_id bigint default 0,
  first_notification INTEGER  default 0,
  last_notification INTEGER  default 0,
  notification_interval double precision  default 0,
  escalate_on_recovery INTEGER  default 0,
  escalate_on_warning INTEGER  default 0,
  escalate_on_unknown INTEGER  default 0,
  escalate_on_critical INTEGER  default 0,
  CONSTRAINT PK_serviceescalation_id PRIMARY KEY (serviceescalation_id) ,
  CONSTRAINT UQ_serviceescalations UNIQUE (instance_id,config_type,service_object_id,timeperiod_object_id,first_notification,last_notification)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}serviceescalation_contactgroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}serviceescalation_contactgroups (
  serviceescalation_contactgroup_id bigserial,
  instance_id bigint default 0,
  serviceescalation_id bigint default 0,
  contactgroup_object_id bigint default 0,
  CONSTRAINT PK_serviceescalation_contactgroup_id PRIMARY KEY (serviceescalation_contactgroup_id) ,
  CONSTRAINT UQ_serviceescalation_contactgro UNIQUE (serviceescalation_id,contactgroup_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}serviceescalation_contacts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}serviceescalation_contacts (
  serviceescalation_contact_id bigserial,
  instance_id bigint default 0,
  serviceescalation_id bigint default 0,
  contact_object_id bigint default 0,
  CONSTRAINT PK_serviceescalation_contact_id PRIMARY KEY (serviceescalation_contact_id) ,
  CONSTRAINT UQ_serviceescalation_contacts UNIQUE (instance_id,serviceescalation_id,contact_object_id)
)  ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicegroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}servicegroups (
  servicegroup_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  servicegroup_object_id bigint default 0,
  alias TEXT  default '',
  CONSTRAINT PK_servicegroup_id PRIMARY KEY (servicegroup_id) ,
  CONSTRAINT UQ_servicegroups UNIQUE (instance_id,config_type,servicegroup_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicegroup_members
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}servicegroup_members (
  servicegroup_member_id bigserial,
  instance_id bigint default 0,
  servicegroup_id bigint default 0,
  service_object_id bigint default 0,
  CONSTRAINT PK_servicegroup_member_id PRIMARY KEY (servicegroup_member_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}services
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}services (
  service_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  host_object_id bigint default 0,
  service_object_id bigint default 0,
  display_name TEXT  default '',
  check_command_object_id bigint default 0,
  check_command_args TEXT  default '',
  eventhandler_command_object_id bigint default 0,
  eventhandler_command_args TEXT  default '',
  notification_timeperiod_object_id bigint default 0,
  check_timeperiod_object_id bigint default 0,
  failure_prediction_options TEXT  default '',
  check_interval double precision  default 0,
  retry_interval double precision  default 0,
  max_check_attempts INTEGER  default 0,
  first_notification_delay double precision  default 0,
  notification_interval double precision  default 0,
  notify_on_warning INTEGER  default 0,
  notify_on_unknown INTEGER  default 0,
  notify_on_critical INTEGER  default 0,
  notify_on_recovery INTEGER  default 0,
  notify_on_flapping INTEGER  default 0,
  notify_on_downtime INTEGER  default 0,
  stalk_on_ok INTEGER  default 0,
  stalk_on_warning INTEGER  default 0,
  stalk_on_unknown INTEGER  default 0,
  stalk_on_critical INTEGER  default 0,
  is_volatile INTEGER  default 0,
  flap_detection_enabled INTEGER  default 0,
  flap_detection_on_ok INTEGER  default 0,
  flap_detection_on_warning INTEGER  default 0,
  flap_detection_on_unknown INTEGER  default 0,
  flap_detection_on_critical INTEGER  default 0,
  low_flap_threshold double precision  default 0,
  high_flap_threshold double precision  default 0,
  process_performance_data INTEGER  default 0,
  freshness_checks_enabled INTEGER  default 0,
  freshness_threshold INTEGER  default 0,
  passive_checks_enabled INTEGER  default 0,
  event_handler_enabled INTEGER  default 0,
  active_checks_enabled INTEGER  default 0,
  retain_status_information INTEGER  default 0,
  retain_nonstatus_information INTEGER  default 0,
  notifications_enabled INTEGER  default 0,
  obsess_over_service INTEGER  default 0,
  failure_prediction_enabled INTEGER  default 0,
  notes TEXT  default '',
  notes_url TEXT  default '',
  action_url TEXT  default '',
  icon_image TEXT  default '',
  icon_image_alt TEXT  default '',
  CONSTRAINT PK_service_id PRIMARY KEY (service_id) ,
  CONSTRAINT UQ_services UNIQUE (instance_id,config_type,service_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicestatus
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}servicestatus (
  servicestatus_id bigserial,
  instance_id bigint default 0,
  service_object_id bigint default 0,
  status_update_time timestamp with time zone default '1970-01-01 00:00:00',
  output TEXT  default '',
  long_output TEXT  default '',
  perfdata TEXT  default '',
  check_source TEXT  default '',
  current_state INTEGER  default 0,
  has_been_checked INTEGER  default 0,
  should_be_scheduled INTEGER  default 0,
  current_check_attempt INTEGER  default 0,
  max_check_attempts INTEGER  default 0,
  last_check timestamp with time zone default '1970-01-01 00:00:00',
  next_check timestamp with time zone default '1970-01-01 00:00:00',
  check_type INTEGER  default 0,
  last_state_change timestamp with time zone default '1970-01-01 00:00:00',
  last_hard_state_change timestamp with time zone default '1970-01-01 00:00:00',
  last_hard_state INTEGER  default 0,
  last_time_ok timestamp with time zone default '1970-01-01 00:00:00',
  last_time_warning timestamp with time zone default '1970-01-01 00:00:00',
  last_time_unknown timestamp with time zone default '1970-01-01 00:00:00',
  last_time_critical timestamp with time zone default '1970-01-01 00:00:00',
  state_type INTEGER  default 0,
  last_notification timestamp with time zone default '1970-01-01 00:00:00',
  next_notification timestamp with time zone default '1970-01-01 00:00:00',
  no_more_notifications INTEGER  default 0,
  notifications_enabled INTEGER  default 0,
  problem_has_been_acknowledged INTEGER  default 0,
  acknowledgement_type INTEGER  default 0,
  current_notification_number INTEGER  default 0,
  passive_checks_enabled INTEGER  default 0,
  active_checks_enabled INTEGER  default 0,
  event_handler_enabled INTEGER  default 0,
  flap_detection_enabled INTEGER  default 0,
  is_flapping INTEGER  default 0,
  percent_state_change double precision  default 0,
  latency double precision  default 0,
  execution_time double precision  default 0,
  scheduled_downtime_depth INTEGER  default 0,
  failure_prediction_enabled INTEGER  default 0,
  process_performance_data INTEGER  default 0,
  obsess_over_service INTEGER  default 0,
  modified_service_attributes INTEGER  default 0,
  event_handler TEXT  default '',
  check_command TEXT  default '',
  normal_check_interval double precision  default 0,
  retry_check_interval double precision  default 0,
  check_timeperiod_object_id bigint default 0,
  CONSTRAINT PK_servicestatus_id PRIMARY KEY (servicestatus_id) ,
  CONSTRAINT UQ_servicestatus UNIQUE (service_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}service_contactgroups
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}service_contactgroups (
  service_contactgroup_id bigserial,
  instance_id bigint default 0,
  service_id bigint default 0,
  contactgroup_object_id bigint default 0,
  CONSTRAINT PK_service_contactgroup_id PRIMARY KEY (service_contactgroup_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}service_contacts
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}service_contacts (
  service_contact_id bigserial,
  instance_id bigint default 0,
  service_id bigint default 0,
  contact_object_id bigint default 0,
  CONSTRAINT PK_service_contact_id PRIMARY KEY (service_contact_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}statehistory
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}statehistory (
  statehistory_id bigserial,
  instance_id bigint default 0,
  state_time timestamp with time zone default '1970-01-01 00:00:00',
  state_time_usec INTEGER  default 0,
  object_id bigint default 0,
  state_change INTEGER  default 0,
  state INTEGER  default 0,
  state_type INTEGER  default 0,
  current_check_attempt INTEGER  default 0,
  max_check_attempts INTEGER  default 0,
  last_state INTEGER  default '-1',
  last_hard_state INTEGER  default '-1',
  output TEXT  default '',
  long_output TEXT  default '',
  CONSTRAINT PK_statehistory_id PRIMARY KEY (statehistory_id) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}systemcommands
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}systemcommands (
  systemcommand_id bigserial,
  instance_id bigint default 0,
  start_time timestamp with time zone default '1970-01-01 00:00:00',
  start_time_usec INTEGER  default 0,
  end_time timestamp with time zone default '1970-01-01 00:00:00',
  end_time_usec INTEGER  default 0,
  command_line TEXT  default '',
  timeout INTEGER  default 0,
  early_timeout INTEGER  default 0,
  execution_time double precision  default 0,
  return_code INTEGER  default 0,
  output TEXT  default '',
  long_output TEXT  default '',
  CONSTRAINT PK_systemcommand_id PRIMARY KEY (systemcommand_id) ,
  CONSTRAINT UQ_systemcommands UNIQUE (instance_id,start_time,start_time_usec)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}timeperiods
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}timeperiods (
  timeperiod_id bigserial,
  instance_id bigint default 0,
  config_type INTEGER  default 0,
  timeperiod_object_id bigint default 0,
  alias TEXT  default '',
  CONSTRAINT PK_timeperiod_id PRIMARY KEY (timeperiod_id) ,
  CONSTRAINT UQ_timeperiods UNIQUE (instance_id,config_type,timeperiod_object_id)
) ;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}timeperiod_timeranges
--

CREATE TABLE  {{data.modules.ido2db.database.prefix}}timeperiod_timeranges (
  timeperiod_timerange_id bigserial,
  instance_id bigint default 0,
  timeperiod_id bigint default 0,
  day INTEGER  default 0,
  start_sec INTEGER  default 0,
  end_sec INTEGER  default 0,
  CONSTRAINT PK_timeperiod_timerange_id PRIMARY KEY (timeperiod_timerange_id)
) ;


-- -----------------------------------------
-- add index (delete)
-- -----------------------------------------

-- for periodic delete
-- instance_id and
-- TIMEDEVENTS => scheduled_time
-- SYSTEMCOMMANDS, SERVICECHECKS, HOSTCHECKS, EVENTHANDLERS  => start_time
-- EXTERNALCOMMANDS => entry_time

-- instance_id
CREATE INDEX systemcommands_i_id_idx on {{data.modules.ido2db.database.prefix}}systemcommands(instance_id);
CREATE INDEX servicechecks_i_id_idx on {{data.modules.ido2db.database.prefix}}servicechecks(instance_id);
CREATE INDEX hostchecks_i_id_idx on {{data.modules.ido2db.database.prefix}}hostchecks(instance_id);
CREATE INDEX eventhandlers_i_id_idx on {{data.modules.ido2db.database.prefix}}eventhandlers(instance_id);
CREATE INDEX externalcommands_i_id_idx on {{data.modules.ido2db.database.prefix}}externalcommands(instance_id);

-- time
CREATE INDEX systemcommands_time_id_idx on {{data.modules.ido2db.database.prefix}}systemcommands(start_time);
CREATE INDEX servicechecks_time_id_idx on {{data.modules.ido2db.database.prefix}}servicechecks(start_time);
CREATE INDEX hostchecks_time_id_idx on {{data.modules.ido2db.database.prefix}}hostchecks(start_time);
CREATE INDEX eventhandlers_time_id_idx on {{data.modules.ido2db.database.prefix}}eventhandlers(start_time);
CREATE INDEX externalcommands_time_id_idx on {{data.modules.ido2db.database.prefix}}externalcommands(entry_time);


-- for starting cleanup - referenced in dbhandler.c:882
-- instance_id only

-- realtime data
CREATE INDEX programstatus_i_id_idx on {{data.modules.ido2db.database.prefix}}programstatus(instance_id);
CREATE INDEX hoststatus_i_id_idx on {{data.modules.ido2db.database.prefix}}hoststatus(instance_id);
CREATE INDEX servicestatus_i_id_idx on {{data.modules.ido2db.database.prefix}}servicestatus(instance_id);
CREATE INDEX contactstatus_i_id_idx on {{data.modules.ido2db.database.prefix}}contactstatus(instance_id);
CREATE INDEX comments_i_id_idx on {{data.modules.ido2db.database.prefix}}comments(instance_id);
CREATE INDEX scheduleddowntime_i_id_idx on {{data.modules.ido2db.database.prefix}}scheduleddowntime(instance_id);
CREATE INDEX runtimevariables_i_id_idx on {{data.modules.ido2db.database.prefix}}runtimevariables(instance_id);
CREATE INDEX customvariablestatus_i_id_idx on {{data.modules.ido2db.database.prefix}}customvariablestatus(instance_id);

-- config data
CREATE INDEX configfiles_i_id_idx on {{data.modules.ido2db.database.prefix}}configfiles(instance_id);
CREATE INDEX configfilevariables_i_id_idx on {{data.modules.ido2db.database.prefix}}configfilevariables(instance_id);
CREATE INDEX customvariables_i_id_idx on {{data.modules.ido2db.database.prefix}}customvariables(instance_id);
CREATE INDEX commands_i_id_idx on {{data.modules.ido2db.database.prefix}}commands(instance_id);
CREATE INDEX timeperiods_i_id_idx on {{data.modules.ido2db.database.prefix}}timeperiods(instance_id);
CREATE INDEX timeperiod_timeranges_i_id_idx on {{data.modules.ido2db.database.prefix}}timeperiod_timeranges(instance_id);
CREATE INDEX contactgroups_i_id_idx on {{data.modules.ido2db.database.prefix}}contactgroups(instance_id);
CREATE INDEX contactgroup_members_i_id_idx on {{data.modules.ido2db.database.prefix}}contactgroup_members(instance_id);
CREATE INDEX hostgroups_i_id_idx on {{data.modules.ido2db.database.prefix}}hostgroups(instance_id);
CREATE INDEX hostgroup_members_i_id_idx on {{data.modules.ido2db.database.prefix}}hostgroup_members(instance_id);
CREATE INDEX servicegroups_i_id_idx on {{data.modules.ido2db.database.prefix}}servicegroups(instance_id);
CREATE INDEX servicegroup_members_i_id_idx on {{data.modules.ido2db.database.prefix}}servicegroup_members(instance_id);
CREATE INDEX hostesc_i_id_idx on {{data.modules.ido2db.database.prefix}}hostescalations(instance_id);
CREATE INDEX hostesc_contacts_i_id_idx on {{data.modules.ido2db.database.prefix}}hostescalation_contacts(instance_id);
CREATE INDEX serviceesc_i_id_idx on {{data.modules.ido2db.database.prefix}}serviceescalations(instance_id);
CREATE INDEX serviceesc_contacts_i_id_idx on {{data.modules.ido2db.database.prefix}}serviceescalation_contacts(instance_id);
CREATE INDEX hostdependencies_i_id_idx on {{data.modules.ido2db.database.prefix}}hostdependencies(instance_id);
CREATE INDEX contacts_i_id_idx on {{data.modules.ido2db.database.prefix}}contacts(instance_id);
CREATE INDEX contact_addresses_i_id_idx on {{data.modules.ido2db.database.prefix}}contact_addresses(instance_id);
CREATE INDEX contact_notifcommands_i_id_idx on {{data.modules.ido2db.database.prefix}}contact_notificationcommands(instance_id);
CREATE INDEX hosts_i_id_idx on {{data.modules.ido2db.database.prefix}}hosts(instance_id);
CREATE INDEX host_parenthosts_i_id_idx on {{data.modules.ido2db.database.prefix}}host_parenthosts(instance_id);
CREATE INDEX host_contacts_i_id_idx on {{data.modules.ido2db.database.prefix}}host_contacts(instance_id);
CREATE INDEX services_i_id_idx on {{data.modules.ido2db.database.prefix}}services(instance_id);
CREATE INDEX service_contacts_i_id_idx on {{data.modules.ido2db.database.prefix}}service_contacts(instance_id);
CREATE INDEX service_contactgroups_i_id_idx on {{data.modules.ido2db.database.prefix}}service_contactgroups(instance_id);
CREATE INDEX host_contactgroups_i_id_idx on {{data.modules.ido2db.database.prefix}}host_contactgroups(instance_id);
CREATE INDEX hostesc_cgroups_i_id_idx on {{data.modules.ido2db.database.prefix}}hostescalation_contactgroups(instance_id);
CREATE INDEX serviceesc_cgroups_i_id_idx on {{data.modules.ido2db.database.prefix}}serviceescalation_contactgroups(instance_id);

-- -----------------------------------------
-- more index stuff (WHERE clauses)
-- -----------------------------------------

-- hosts
CREATE INDEX hosts_host_object_id_idx on {{data.modules.ido2db.database.prefix}}hosts(host_object_id);

-- hoststatus
CREATE INDEX hoststatus_stat_upd_time_idx on {{data.modules.ido2db.database.prefix}}hoststatus(status_update_time);
CREATE INDEX hoststatus_current_state_idx on {{data.modules.ido2db.database.prefix}}hoststatus(current_state);
CREATE INDEX hoststatus_check_type_idx on {{data.modules.ido2db.database.prefix}}hoststatus(check_type);
CREATE INDEX hoststatus_state_type_idx on {{data.modules.ido2db.database.prefix}}hoststatus(state_type);
CREATE INDEX hoststatus_last_state_chg_idx on {{data.modules.ido2db.database.prefix}}hoststatus(last_state_change);
CREATE INDEX hoststatus_notif_enabled_idx on {{data.modules.ido2db.database.prefix}}hoststatus(notifications_enabled);
CREATE INDEX hoststatus_problem_ack_idx on {{data.modules.ido2db.database.prefix}}hoststatus(problem_has_been_acknowledged);
CREATE INDEX hoststatus_act_chks_en_idx on {{data.modules.ido2db.database.prefix}}hoststatus(active_checks_enabled);
CREATE INDEX hoststatus_pas_chks_en_idx on {{data.modules.ido2db.database.prefix}}hoststatus(passive_checks_enabled);
CREATE INDEX hoststatus_event_hdl_en_idx on {{data.modules.ido2db.database.prefix}}hoststatus(event_handler_enabled);
CREATE INDEX hoststatus_flap_det_en_idx on {{data.modules.ido2db.database.prefix}}hoststatus(flap_detection_enabled);
CREATE INDEX hoststatus_is_flapping_idx on {{data.modules.ido2db.database.prefix}}hoststatus(is_flapping);
CREATE INDEX hoststatus_p_state_chg_idx on {{data.modules.ido2db.database.prefix}}hoststatus(percent_state_change);
CREATE INDEX hoststatus_latency_idx on {{data.modules.ido2db.database.prefix}}hoststatus(latency);
CREATE INDEX hoststatus_ex_time_idx on {{data.modules.ido2db.database.prefix}}hoststatus(execution_time);
CREATE INDEX hoststatus_sch_downt_d_idx on {{data.modules.ido2db.database.prefix}}hoststatus(scheduled_downtime_depth);

-- services
CREATE INDEX services_host_object_id_idx on {{data.modules.ido2db.database.prefix}}services(host_object_id);

--servicestatus
CREATE INDEX srvcstatus_stat_upd_time_idx on {{data.modules.ido2db.database.prefix}}servicestatus(status_update_time);
CREATE INDEX srvcstatus_current_state_idx on {{data.modules.ido2db.database.prefix}}servicestatus(current_state);
CREATE INDEX srvcstatus_check_type_idx on {{data.modules.ido2db.database.prefix}}servicestatus(check_type);
CREATE INDEX srvcstatus_state_type_idx on {{data.modules.ido2db.database.prefix}}servicestatus(state_type);
CREATE INDEX srvcstatus_last_state_chg_idx on {{data.modules.ido2db.database.prefix}}servicestatus(last_state_change);
CREATE INDEX srvcstatus_notif_enabled_idx on {{data.modules.ido2db.database.prefix}}servicestatus(notifications_enabled);
CREATE INDEX srvcstatus_problem_ack_idx on {{data.modules.ido2db.database.prefix}}servicestatus(problem_has_been_acknowledged);
CREATE INDEX srvcstatus_act_chks_en_idx on {{data.modules.ido2db.database.prefix}}servicestatus(active_checks_enabled);
CREATE INDEX srvcstatus_pas_chks_en_idx on {{data.modules.ido2db.database.prefix}}servicestatus(passive_checks_enabled);
CREATE INDEX srvcstatus_event_hdl_en_idx on {{data.modules.ido2db.database.prefix}}servicestatus(event_handler_enabled);
CREATE INDEX srvcstatus_flap_det_en_idx on {{data.modules.ido2db.database.prefix}}servicestatus(flap_detection_enabled);
CREATE INDEX srvcstatus_is_flapping_idx on {{data.modules.ido2db.database.prefix}}servicestatus(is_flapping);
CREATE INDEX srvcstatus_p_state_chg_idx on {{data.modules.ido2db.database.prefix}}servicestatus(percent_state_change);
CREATE INDEX srvcstatus_latency_idx on {{data.modules.ido2db.database.prefix}}servicestatus(latency);
CREATE INDEX srvcstatus_ex_time_idx on {{data.modules.ido2db.database.prefix}}servicestatus(execution_time);
CREATE INDEX srvcstatus_sch_downt_d_idx on {{data.modules.ido2db.database.prefix}}servicestatus(scheduled_downtime_depth);

-- hostchecks
CREATE INDEX hostchks_h_obj_id_idx on {{data.modules.ido2db.database.prefix}}hostchecks(host_object_id);

-- servicechecks
CREATE INDEX servicechks_s_obj_id_idx on {{data.modules.ido2db.database.prefix}}servicechecks(service_object_id);

-- objects
CREATE INDEX objects_objtype_id_idx ON {{data.modules.ido2db.database.prefix}}objects(objecttype_id);
CREATE INDEX objects_name1_idx ON {{data.modules.ido2db.database.prefix}}objects(name1);
CREATE INDEX objects_name2_idx ON {{data.modules.ido2db.database.prefix}}objects(name2);
CREATE INDEX objects_inst_id_idx ON {{data.modules.ido2db.database.prefix}}objects(instance_id);

-- instances
-- CREATE INDEX instances_name_idx on {{data.modules.ido2db.database.prefix}}instances(instance_name);

-- logentries
-- CREATE INDEX loge_instance_id_idx on {{data.modules.ido2db.database.prefix}}logentries(instance_id);
-- #236
CREATE INDEX loge_time_idx on {{data.modules.ido2db.database.prefix}}logentries(logentry_time);
-- CREATE INDEX loge_data_idx on {{data.modules.ido2db.database.prefix}}logentries(logentry_data);
CREATE INDEX loge_inst_id_time_idx on {{data.modules.ido2db.database.prefix}}logentries (instance_id, logentry_time);


-- commenthistory
-- CREATE INDEX c_hist_instance_id_idx on {{data.modules.ido2db.database.prefix}}logentries(instance_id);
-- CREATE INDEX c_hist_c_time_idx on {{data.modules.ido2db.database.prefix}}logentries(comment_time);
-- CREATE INDEX c_hist_i_c_id_idx on {{data.modules.ido2db.database.prefix}}logentries(internal_comment_id);

-- downtimehistory
-- CREATE INDEX d_t_hist_nstance_id_idx on {{data.modules.ido2db.database.prefix}}downtimehistory(instance_id);
-- CREATE INDEX d_t_hist_type_idx on {{data.modules.ido2db.database.prefix}}downtimehistory(downtime_type);
-- CREATE INDEX d_t_hist_object_id_idx on {{data.modules.ido2db.database.prefix}}downtimehistory(object_id);
-- CREATE INDEX d_t_hist_entry_time_idx on {{data.modules.ido2db.database.prefix}}downtimehistory(entry_time);
-- CREATE INDEX d_t_hist_sched_start_idx on {{data.modules.ido2db.database.prefix}}downtimehistory(scheduled_start_time);
-- CREATE INDEX d_t_hist_sched_end_idx on {{data.modules.ido2db.database.prefix}}downtimehistory(scheduled_end_time);

-- scheduleddowntime
-- CREATE INDEX sched_d_t_downtime_type_idx on {{data.modules.ido2db.database.prefix}}scheduleddowntime(downtime_type);
-- CREATE INDEX sched_d_t_object_id_idx on {{data.modules.ido2db.database.prefix}}scheduleddowntime(object_id);
-- CREATE INDEX sched_d_t_entry_time_idx on {{data.modules.ido2db.database.prefix}}scheduleddowntime(entry_time);
-- CREATE INDEX sched_d_t_start_time_idx on {{data.modules.ido2db.database.prefix}}scheduleddowntime(scheduled_start_time);
-- CREATE INDEX sched_d_t_end_time_idx on {{data.modules.ido2db.database.prefix}}scheduleddowntime(scheduled_end_time);

-- Icinga Web Notifications
CREATE INDEX notification_idx ON {{data.modules.ido2db.database.prefix}}notifications(notification_type, object_id, start_time);
CREATE INDEX notification_object_id_idx ON {{data.modules.ido2db.database.prefix}}notifications(object_id);
CREATE INDEX contact_notification_idx ON {{data.modules.ido2db.database.prefix}}contactnotifications(notification_id, contact_object_id);
CREATE INDEX contacts_object_id_idx ON {{data.modules.ido2db.database.prefix}}contacts(contact_object_id);
CREATE INDEX contact_notif_meth_notif_idx ON {{data.modules.ido2db.database.prefix}}contactnotificationmethods(contactnotification_id, command_object_id);
CREATE INDEX command_object_idx ON {{data.modules.ido2db.database.prefix}}commands(object_id);                         
CREATE INDEX services_combined_object_idx ON {{data.modules.ido2db.database.prefix}}services(service_object_id, host_object_id);

-- statehistory
CREATE INDEX statehist_i_id_o_id_s_ty_s_ti on {{data.modules.ido2db.database.prefix}}statehistory(instance_id, object_id, state_type, state_time);
--#2274
create index statehist_state_idx on {{data.modules.ido2db.database.prefix}}statehistory(object_id,state);

-- #2618
CREATE INDEX cntgrpmbrs_cgid_coid ON {{data.modules.ido2db.database.prefix}}contactgroup_members (contactgroup_id,contact_object_id);
CREATE INDEX hstgrpmbrs_hgid_hoid ON {{data.modules.ido2db.database.prefix}}hostgroup_members (hostgroup_id,host_object_id);
CREATE INDEX hstcntgrps_hid_cgoid ON {{data.modules.ido2db.database.prefix}}host_contactgroups (host_id,contactgroup_object_id);
CREATE INDEX hstprnthsts_hid_phoid ON {{data.modules.ido2db.database.prefix}}host_parenthosts (host_id,parent_host_object_id);
CREATE INDEX runtimevars_iid_varn ON {{data.modules.ido2db.database.prefix}}runtimevariables (instance_id,varname);
CREATE INDEX sgmbrs_sgid_soid ON {{data.modules.ido2db.database.prefix}}servicegroup_members (servicegroup_id,service_object_id);
CREATE INDEX scgrps_sid_cgoid ON {{data.modules.ido2db.database.prefix}}service_contactgroups (service_id,contactgroup_object_id);
CREATE INDEX tperiod_tid_d_ss_es ON {{data.modules.ido2db.database.prefix}}timeperiod_timeranges (timeperiod_id,day,start_sec,end_sec);

-- #3649
CREATE INDEX sla_idx_sthist ON {{data.modules.ido2db.database.prefix}}statehistory (object_id, state_time DESC);
CREATE INDEX sla_idx_dohist ON {{data.modules.ido2db.database.prefix}}downtimehistory (object_id, actual_start_time, actual_end_time);
CREATE INDEX sla_idx_obj ON {{data.modules.ido2db.database.prefix}}objects (objecttype_id, is_active, name1);


-- -----------------------------------------
-- set dbversion
-- -----------------------------------------

SELECT updatedbversion('1.10.0');

