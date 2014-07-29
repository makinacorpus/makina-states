{% set data = salt['mc_utils.json_load'](data) %}
-- MANAGED VIA SALT -- DO NOT EDIT
-- from /usr/share/doc/icinga-idoutils/examples/mysql/mysql.sql
-- --------------------------------------------------------
-- mysql.sql
-- DB definition for MySQL
--
-- Copyright (c) 2009-2013 Icinga Development Team (http://www.icinga.org)
--
-- -- --------------------------------------------------------

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;


--
-- Database: icinga
--

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}acknowledgements
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}acknowledgements (
  acknowledgement_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  entry_time timestamp  default '0000-00-00 00:00:00',
  entry_time_usec  int default 0,
  acknowledgement_type smallint default 0,
  object_id bigint unsigned default 0,
  state smallint default 0,
  author_name varchar(64) character set latin1  default '',
  comment_data TEXT character set latin1  default '',
  is_sticky smallint default 0,
  persistent_comment smallint default 0,
  notify_contacts smallint default 0,
  end_time timestamp default '0000-00-00 00:00:00',
  PRIMARY KEY  (acknowledgement_id)
) ENGINE=InnoDB COMMENT='Current and historical host and service acknowledgements';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}commands
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}commands (
  command_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  object_id bigint unsigned default 0,
  command_line TEXT character set latin1  default '',
  PRIMARY KEY  (command_id),
  UNIQUE KEY instance_id (instance_id,object_id,config_type)
) ENGINE=InnoDB  COMMENT='Command definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}commenthistory
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}commenthistory (
  commenthistory_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  entry_time timestamp  default '0000-00-00 00:00:00',
  entry_time_usec  int default 0,
  comment_type smallint default 0,
  entry_type smallint default 0,
  object_id bigint unsigned default 0,
  comment_time timestamp  default '0000-00-00 00:00:00',
  internal_comment_id bigint unsigned default 0,
  author_name varchar(64) character set latin1  default '',
  comment_data TEXT character set latin1  default '',
  is_persistent smallint default 0,
  comment_source smallint default 0,
  expires smallint default 0,
  expiration_time timestamp  default '0000-00-00 00:00:00',
  deletion_time timestamp  default '0000-00-00 00:00:00',
  deletion_time_usec  int default 0,
  PRIMARY KEY  (commenthistory_id),
  UNIQUE KEY instance_id (instance_id,object_id,comment_time,internal_comment_id)
) ENGINE=InnoDB  COMMENT='Historical host and service comments';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}comments
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}comments (
  comment_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  entry_time timestamp  default '0000-00-00 00:00:00',
  entry_time_usec  int default 0,
  comment_type smallint default 0,
  entry_type smallint default 0,
  object_id bigint unsigned default 0,
  comment_time timestamp  default '0000-00-00 00:00:00',
  internal_comment_id bigint unsigned default 0,
  author_name varchar(64) character set latin1  default '',
  comment_data TEXT character set latin1  default '',
  is_persistent smallint default 0,
  comment_source smallint default 0,
  expires smallint default 0,
  expiration_time timestamp  default '0000-00-00 00:00:00',
  PRIMARY KEY  (comment_id),
  UNIQUE KEY instance_id (instance_id,object_id,comment_time,internal_comment_id)
) ENGINE=InnoDB  COMMENT='Usercomments on Icinga objects';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}configfiles
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}configfiles (
  configfile_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  configfile_type smallint default 0,
  configfile_path varchar(255) character set latin1  default '',
  PRIMARY KEY  (configfile_id),
  UNIQUE KEY instance_id (instance_id,configfile_type,configfile_path)
) ENGINE=InnoDB  COMMENT='Configuration files';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}configfilevariables
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}configfilevariables (
  configfilevariable_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  configfile_id bigint unsigned default 0,
  varname varchar(64) character set latin1  default '',
  varvalue TEXT character set latin1  default '',
  PRIMARY KEY  (configfilevariable_id)
) ENGINE=InnoDB  COMMENT='Configuration file variables';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}conninfo
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}conninfo (
  conninfo_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  agent_name varchar(32) character set latin1  default '',
  agent_version varchar(16) character set latin1  default '',
  disposition varchar(16) character set latin1  default '',
  connect_source varchar(16) character set latin1  default '',
  connect_type varchar(16) character set latin1  default '',
  connect_time timestamp  default '0000-00-00 00:00:00',
  disconnect_time timestamp  default '0000-00-00 00:00:00',
  last_checkin_time timestamp  default '0000-00-00 00:00:00',
  data_start_time timestamp  default '0000-00-00 00:00:00',
  data_end_time timestamp  default '0000-00-00 00:00:00',
  bytes_processed bigint unsigned  default '0',
  lines_processed bigint unsigned  default '0',
  entries_processed bigint unsigned  default '0',
  PRIMARY KEY  (conninfo_id)
) ENGINE=InnoDB  COMMENT='IDO2DB daemon connection information';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactgroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contactgroups (
  contactgroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  contactgroup_object_id bigint unsigned default 0,
  alias TEXT character set latin1  default '',
  PRIMARY KEY  (contactgroup_id),
  UNIQUE KEY instance_id (instance_id,config_type,contactgroup_object_id)
) ENGINE=InnoDB  COMMENT='Contactgroup definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactgroup_members
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contactgroup_members (
  contactgroup_member_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  contactgroup_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  PRIMARY KEY  (contactgroup_member_id)
) ENGINE=InnoDB  COMMENT='Contactgroup members';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactnotificationmethods
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contactnotificationmethods (
  contactnotificationmethod_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  contactnotification_id bigint unsigned default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  command_object_id bigint unsigned default 0,
  command_args TEXT character set latin1  default '',
  PRIMARY KEY  (contactnotificationmethod_id),
  UNIQUE KEY instance_id (instance_id,contactnotification_id,start_time,start_time_usec)
) ENGINE=InnoDB  COMMENT='Historical record of contact notification methods';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactnotifications
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contactnotifications (
  contactnotification_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  notification_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  PRIMARY KEY  (contactnotification_id),
  UNIQUE KEY instance_id (instance_id,contact_object_id,start_time,start_time_usec)
) ENGINE=InnoDB  COMMENT='Historical record of contact notifications';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contacts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contacts (
  contact_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  contact_object_id bigint unsigned default 0,
  alias varchar(64) character set latin1  default '',
  email_address varchar(255) character set latin1  default '',
  pager_address varchar(64) character set latin1  default '',
  host_timeperiod_object_id bigint unsigned default 0,
  service_timeperiod_object_id bigint unsigned default 0,
  host_notifications_enabled smallint default 0,
  service_notifications_enabled smallint default 0,
  can_submit_commands smallint default 0,
  notify_service_recovery smallint default 0,
  notify_service_warning smallint default 0,
  notify_service_unknown smallint default 0,
  notify_service_critical smallint default 0,
  notify_service_flapping smallint default 0,
  notify_service_downtime smallint default 0,
  notify_host_recovery smallint default 0,
  notify_host_down smallint default 0,
  notify_host_unreachable smallint default 0,
  notify_host_flapping smallint default 0,
  notify_host_downtime smallint default 0,
  PRIMARY KEY  (contact_id),
  UNIQUE KEY instance_id (instance_id,config_type,contact_object_id)
) ENGINE=InnoDB  COMMENT='Contact definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contactstatus
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contactstatus (
  contactstatus_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  status_update_time timestamp  default '0000-00-00 00:00:00',
  host_notifications_enabled smallint default 0,
  service_notifications_enabled smallint default 0,
  last_host_notification timestamp  default '0000-00-00 00:00:00',
  last_service_notification timestamp  default '0000-00-00 00:00:00',
  modified_attributes  int default 0,
  modified_host_attributes  int default 0,
  modified_service_attributes  int default 0,
  PRIMARY KEY  (contactstatus_id),
  UNIQUE KEY contact_object_id (contact_object_id)
) ENGINE=InnoDB  COMMENT='Contact status';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contact_addresses
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contact_addresses (
  contact_address_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  contact_id bigint unsigned default 0,
  address_number smallint default 0,
  address varchar(255) character set latin1  default '',
  PRIMARY KEY  (contact_address_id),
  UNIQUE KEY contact_id (contact_id,address_number)
) ENGINE=InnoDB COMMENT='Contact addresses';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}contact_notificationcommands
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}contact_notificationcommands (
  contact_notificationcommand_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  contact_id bigint unsigned default 0,
  notification_type smallint default 0,
  command_object_id bigint unsigned default 0,
  command_args varchar(255) character set latin1  default '',
  PRIMARY KEY  (contact_notificationcommand_id),
  UNIQUE KEY contact_id (contact_id,notification_type,command_object_id,command_args)
) ENGINE=InnoDB  COMMENT='Contact host and service notification commands';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}customvariables
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}customvariables (
  customvariable_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  object_id bigint unsigned default 0,
  config_type smallint default 0,
  has_been_modified smallint default 0,
  varname varchar(255) character set latin1  default '',
  varvalue TEXT character set latin1  default '',
  PRIMARY KEY  (customvariable_id),
  UNIQUE KEY object_id_2 (object_id,config_type,varname),
  KEY varname (varname)
) ENGINE=InnoDB COMMENT='Custom variables';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}customvariablestatus
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}customvariablestatus (
  customvariablestatus_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  object_id bigint unsigned default 0,
  status_update_time timestamp  default '0000-00-00 00:00:00',
  has_been_modified smallint default 0,
  varname varchar(255) character set latin1  default '',
  varvalue TEXT character set latin1  default '',
  PRIMARY KEY  (customvariablestatus_id),
  UNIQUE KEY object_id_2 (object_id,varname),
  KEY varname (varname)
) ENGINE=InnoDB COMMENT='Custom variable status information';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}dbversion
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}dbversion (
  dbversion_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  name varchar(10) character set latin1  default '',
  version varchar(10) character set latin1  default '',
  create_time timestamp default '0000-00-00 00:00:00',
  modify_time timestamp default '0000-00-00 00:00:00',
  PRIMARY KEY (dbversion_id),
  UNIQUE KEY dbversion (name)
) ENGINE=InnoDB;

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}downtimehistory
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}downtimehistory (
  downtimehistory_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  downtime_type smallint default 0,
  object_id bigint unsigned default 0,
  entry_time timestamp  default '0000-00-00 00:00:00',
  author_name varchar(64) character set latin1  default '',
  comment_data TEXT character set latin1  default '',
  internal_downtime_id bigint unsigned default 0,
  triggered_by_id bigint unsigned default 0,
  is_fixed smallint default 0,
  duration bigint(20) default 0,
  scheduled_start_time timestamp  default '0000-00-00 00:00:00',
  scheduled_end_time timestamp  default '0000-00-00 00:00:00',
  was_started smallint default 0,
  actual_start_time timestamp  default '0000-00-00 00:00:00',
  actual_start_time_usec  int default 0,
  actual_end_time timestamp  default '0000-00-00 00:00:00',
  actual_end_time_usec  int default 0,
  was_cancelled smallint default 0,
  is_in_effect smallint default 0,
  trigger_time timestamp  default '0000-00-00 00:00:00',
  PRIMARY KEY  (downtimehistory_id),
  UNIQUE KEY instance_id (instance_id,object_id,entry_time,internal_downtime_id)
) ENGINE=InnoDB  COMMENT='Historical scheduled host and service downtime';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}eventhandlers
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}eventhandlers (
  eventhandler_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  eventhandler_type smallint default 0,
  object_id bigint unsigned default 0,
  state smallint default 0,
  state_type smallint default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  command_object_id bigint unsigned default 0,
  command_args TEXT character set latin1  default '',
  command_line TEXT character set latin1  default '',
  timeout smallint default 0,
  early_timeout smallint default 0,
  execution_time double  default '0',
  return_code smallint default 0,
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  PRIMARY KEY  (eventhandler_id),
  UNIQUE KEY instance_id (instance_id,object_id,start_time,start_time_usec)
) ENGINE=InnoDB COMMENT='Historical host and service event handlers';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}externalcommands
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}externalcommands (
  externalcommand_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  entry_time timestamp  default '0000-00-00 00:00:00',
  command_type smallint default 0,
  command_name varchar(128) character set latin1  default '',
  command_args TEXT character set latin1  default '',
  PRIMARY KEY  (externalcommand_id)
) ENGINE=InnoDB  COMMENT='Historical record of processed external commands';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}flappinghistory
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}flappinghistory (
  flappinghistory_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  event_time timestamp  default '0000-00-00 00:00:00',
  event_time_usec  int default 0,
  event_type smallint default 0,
  reason_type smallint default 0,
  flapping_type smallint default 0,
  object_id bigint unsigned default 0,
  percent_state_change double  default '0',
  low_threshold double  default '0',
  high_threshold double  default '0',
  comment_time timestamp  default '0000-00-00 00:00:00',
  internal_comment_id bigint unsigned default 0,
  PRIMARY KEY  (flappinghistory_id)
) ENGINE=InnoDB  COMMENT='Current and historical record of host and service flapping';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostchecks
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostchecks (
  hostcheck_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  host_object_id bigint unsigned default 0,
  check_type smallint default 0,
  is_raw_check smallint default 0,
  current_check_attempt smallint default 0,
  max_check_attempts smallint default 0,
  state smallint default 0,
  state_type smallint default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  command_object_id bigint unsigned default 0,
  command_args TEXT character set latin1  default '',
  command_line TEXT character set latin1  default '',
  timeout smallint default 0,
  early_timeout smallint default 0,
  execution_time double  default '0',
  latency double  default '0',
  return_code smallint default 0,
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  perfdata TEXT character set latin1  default '',
  PRIMARY KEY  (hostcheck_id)
) ENGINE=InnoDB  COMMENT='Historical host checks';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostdependencies
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostdependencies (
  hostdependency_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  host_object_id bigint unsigned default 0,
  dependent_host_object_id bigint unsigned default 0,
  dependency_type smallint default 0,
  inherits_parent smallint default 0,
  timeperiod_object_id bigint unsigned default 0,
  fail_on_up smallint default 0,
  fail_on_down smallint default 0,
  fail_on_unreachable smallint default 0,
  PRIMARY KEY  (hostdependency_id),
  UNIQUE KEY instance_id (instance_id,config_type,host_object_id,dependent_host_object_id,dependency_type,inherits_parent,fail_on_up,fail_on_down,fail_on_unreachable)
) ENGINE=InnoDB COMMENT='Host dependency definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostescalations
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostescalations (
  hostescalation_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  host_object_id bigint unsigned default 0,
  timeperiod_object_id bigint unsigned default 0,
  first_notification smallint default 0,
  last_notification smallint default 0,
  notification_interval double  default '0',
  escalate_on_recovery smallint default 0,
  escalate_on_down smallint default 0,
  escalate_on_unreachable smallint default 0,
  PRIMARY KEY  (hostescalation_id),
  UNIQUE KEY instance_id (instance_id,config_type,host_object_id,timeperiod_object_id,first_notification,last_notification)
) ENGINE=InnoDB  COMMENT='Host escalation definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostescalation_contactgroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostescalation_contactgroups (
  hostescalation_contactgroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  hostescalation_id bigint unsigned default 0,
  contactgroup_object_id bigint unsigned default 0,
  PRIMARY KEY  (hostescalation_contactgroup_id),
  UNIQUE KEY instance_id (hostescalation_id,contactgroup_object_id)
) ENGINE=InnoDB  COMMENT='Host escalation contact groups';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostescalation_contacts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostescalation_contacts (
  hostescalation_contact_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  hostescalation_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  PRIMARY KEY  (hostescalation_contact_id),
  UNIQUE KEY instance_id (instance_id,hostescalation_id,contact_object_id)
) ENGINE=InnoDB  COMMENT='Host escalation contacts';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostgroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostgroups (
  hostgroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  hostgroup_object_id bigint unsigned default 0,
  alias TEXT character set latin1  default '',
  PRIMARY KEY  (hostgroup_id),
  UNIQUE KEY instance_id (instance_id,hostgroup_object_id)
) ENGINE=InnoDB  COMMENT='Hostgroup definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hostgroup_members
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hostgroup_members (
  hostgroup_member_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  hostgroup_id bigint unsigned default 0,
  host_object_id bigint unsigned default 0,
  PRIMARY KEY  (hostgroup_member_id)
) ENGINE=InnoDB  COMMENT='Hostgroup members';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hosts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hosts (
  host_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  host_object_id bigint unsigned default 0,
  alias varchar(64) character set latin1  default '',
  display_name varchar(255) character set latin1 collate latin1_general_cs  default '',
  address varchar(128) character set latin1  default '',
  address6 varchar(128) character set latin1  default '',
  check_command_object_id bigint unsigned default 0,
  check_command_args TEXT character set latin1  default '',
  eventhandler_command_object_id bigint unsigned default 0,
  eventhandler_command_args TEXT character set latin1  default '',
  notification_timeperiod_object_id bigint unsigned default 0,
  check_timeperiod_object_id bigint unsigned default 0,
  failure_prediction_options varchar(128) character set latin1  default '',
  check_interval double  default '0',
  retry_interval double  default '0',
  max_check_attempts smallint default 0,
  first_notification_delay double  default '0',
  notification_interval double  default '0',
  notify_on_down smallint default 0,
  notify_on_unreachable smallint default 0,
  notify_on_recovery smallint default 0,
  notify_on_flapping smallint default 0,
  notify_on_downtime smallint default 0,
  stalk_on_up smallint default 0,
  stalk_on_down smallint default 0,
  stalk_on_unreachable smallint default 0,
  flap_detection_enabled smallint default 0,
  flap_detection_on_up smallint default 0,
  flap_detection_on_down smallint default 0,
  flap_detection_on_unreachable smallint default 0,
  low_flap_threshold double  default '0',
  high_flap_threshold double  default '0',
  process_performance_data smallint default 0,
  freshness_checks_enabled smallint default 0,
  freshness_threshold smallint default 0,
  passive_checks_enabled smallint default 0,
  event_handler_enabled smallint default 0,
  active_checks_enabled smallint default 0,
  retain_status_information smallint default 0,
  retain_nonstatus_information smallint default 0,
  notifications_enabled smallint default 0,
  obsess_over_host smallint default 0,
  failure_prediction_enabled smallint default 0,
  notes TEXT character set latin1  default '',
  notes_url TEXT character set latin1  default '',
  action_url TEXT character set latin1  default '',
  icon_image TEXT character set latin1  default '',
  icon_image_alt TEXT character set latin1  default '',
  vrml_image TEXT character set latin1  default '',
  statusmap_image TEXT character set latin1  default '',
  have_2d_coords smallint default 0,
  x_2d smallint default 0,
  y_2d smallint default 0,
  have_3d_coords smallint default 0,
  x_3d double  default '0',
  y_3d double  default '0',
  z_3d double  default '0',
  PRIMARY KEY  (host_id),
  UNIQUE KEY instance_id (instance_id,config_type,host_object_id),
  KEY host_object_id (host_object_id)
) ENGINE=InnoDB  COMMENT='Host definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}hoststatus
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}hoststatus (
  hoststatus_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  host_object_id bigint unsigned default 0,
  status_update_time timestamp  default '0000-00-00 00:00:00',
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  perfdata TEXT character set latin1  default '',
  check_source TEXT character set latin1  default '',
  current_state smallint default 0,
  has_been_checked smallint default 0,
  should_be_scheduled smallint default 0,
  current_check_attempt smallint default 0,
  max_check_attempts smallint default 0,
  last_check timestamp  default '0000-00-00 00:00:00',
  next_check timestamp  default '0000-00-00 00:00:00',
  check_type smallint default 0,
  last_state_change timestamp  default '0000-00-00 00:00:00',
  last_hard_state_change timestamp  default '0000-00-00 00:00:00',
  last_hard_state smallint default 0,
  last_time_up timestamp  default '0000-00-00 00:00:00',
  last_time_down timestamp  default '0000-00-00 00:00:00',
  last_time_unreachable timestamp  default '0000-00-00 00:00:00',
  state_type smallint default 0,
  last_notification timestamp  default '0000-00-00 00:00:00',
  next_notification timestamp  default '0000-00-00 00:00:00',
  no_more_notifications smallint default 0,
  notifications_enabled smallint default 0,
  problem_has_been_acknowledged smallint default 0,
  acknowledgement_type smallint default 0,
  current_notification_number smallint default 0,
  passive_checks_enabled smallint default 0,
  active_checks_enabled smallint default 0,
  event_handler_enabled smallint default 0,
  flap_detection_enabled smallint default 0,
  is_flapping smallint default 0,
  percent_state_change double  default '0',
  latency double  default '0',
  execution_time double  default '0',
  scheduled_downtime_depth smallint default 0,
  failure_prediction_enabled smallint default 0,
  process_performance_data smallint default 0,
  obsess_over_host smallint default 0,
  modified_host_attributes  int default 0,
  event_handler TEXT character set latin1  default '',
  check_command TEXT character set latin1  default '',
  normal_check_interval double  default '0',
  retry_check_interval double  default '0',
  check_timeperiod_object_id bigint unsigned default 0,
  PRIMARY KEY  (hoststatus_id),
  UNIQUE KEY object_id (host_object_id)
) ENGINE=InnoDB  COMMENT='Current host status information';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}host_contactgroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}host_contactgroups (
  host_contactgroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  host_id bigint unsigned default 0,
  contactgroup_object_id bigint unsigned default 0,
  PRIMARY KEY  (host_contactgroup_id)
) ENGINE=InnoDB  COMMENT='Host contact groups';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}host_contacts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}host_contacts (
  host_contact_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  host_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  PRIMARY KEY  (host_contact_id)
) ENGINE=InnoDB  COMMENT='Host contacts';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}host_parenthosts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}host_parenthosts (
  host_parenthost_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  host_id bigint unsigned default 0,
  parent_host_object_id bigint unsigned default 0,
  PRIMARY KEY  (host_parenthost_id)
) ENGINE=InnoDB  COMMENT='Parent hosts';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}instances
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}instances (
  instance_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_name varchar(64) character set latin1  default '',
  instance_description varchar(128) character set latin1  default '',
  PRIMARY KEY  (instance_id)
) ENGINE=InnoDB  COMMENT='Location names of various Icinga installations';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}logentries
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}logentries (
  logentry_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  logentry_time timestamp  default '0000-00-00 00:00:00',
  entry_time timestamp  default '0000-00-00 00:00:00',
  entry_time_usec  int default 0,
  logentry_type  int default 0,
  logentry_data TEXT character set latin1  default '',
  realtime_data smallint default 0,
  inferred_data_extracted smallint default 0,
  object_id bigint unsigned default NULL,
  PRIMARY KEY  (logentry_id)
) ENGINE=InnoDB COMMENT='Historical record of log entries';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}notifications
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}notifications (
  notification_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  notification_type smallint default 0,
  notification_reason smallint default 0,
  object_id bigint unsigned default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  state smallint default 0,
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  escalated smallint default 0,
  contacts_notified smallint default 0,
  PRIMARY KEY  (notification_id),
  UNIQUE KEY instance_id (instance_id,object_id,start_time,start_time_usec)
) ENGINE=InnoDB  COMMENT='Historical record of host and service notifications';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}objects
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}objects (
  object_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  objecttype_id bigint unsigned default 0,
  name1 varchar(128) character set latin1 collate latin1_general_cs  default '',
  name2 varchar(128) character set latin1 collate latin1_general_cs default NULL,
  is_active smallint default 0,
  PRIMARY KEY  (object_id),
  KEY objecttype_id (objecttype_id,name1,name2)
) ENGINE=InnoDB  COMMENT='Current and historical objects of all kinds';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}processevents
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}processevents (
  processevent_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  event_type smallint default 0,
  event_time timestamp  default '0000-00-00 00:00:00',
  event_time_usec  int default 0,
  process_id bigint unsigned default 0,
  program_name varchar(16) character set latin1  default '',
  program_version varchar(20) character set latin1  default '',
  program_date varchar(10) character set latin1  default '',
  PRIMARY KEY  (processevent_id)
) ENGINE=InnoDB  COMMENT='Historical Icinga process events';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}programstatus
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}programstatus (
  programstatus_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  status_update_time timestamp  default '0000-00-00 00:00:00',
  program_start_time timestamp  default '0000-00-00 00:00:00',
  program_end_time timestamp  default '0000-00-00 00:00:00',
  is_currently_running smallint default 0,
  process_id bigint unsigned default 0,
  daemon_mode smallint default 0,
  last_command_check timestamp  default '0000-00-00 00:00:00',
  last_log_rotation timestamp  default '0000-00-00 00:00:00',
  notifications_enabled smallint default 0,
  disable_notif_expire_time timestamp default '0000-00-00 00:00:00',
  active_service_checks_enabled smallint default 0,
  passive_service_checks_enabled smallint default 0,
  active_host_checks_enabled smallint default 0,
  passive_host_checks_enabled smallint default 0,
  event_handlers_enabled smallint default 0,
  flap_detection_enabled smallint default 0,
  failure_prediction_enabled smallint default 0,
  process_performance_data smallint default 0,
  obsess_over_hosts smallint default 0,
  obsess_over_services smallint default 0,
  modified_host_attributes  int default 0,
  modified_service_attributes  int default 0,
  global_host_event_handler TEXT character set latin1  default '',
  global_service_event_handler TEXT character set latin1  default '',
  PRIMARY KEY  (programstatus_id),
  UNIQUE KEY instance_id (instance_id)
) ENGINE=InnoDB  COMMENT='Current program status information';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}runtimevariables
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}runtimevariables (
  runtimevariable_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  varname varchar(64) character set latin1  default '',
  varvalue TEXT character set latin1  default '',
  PRIMARY KEY  (runtimevariable_id)
) ENGINE=InnoDB  COMMENT='Runtime variables from the Icinga daemon';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}scheduleddowntime
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}scheduleddowntime (
  scheduleddowntime_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  downtime_type smallint default 0,
  object_id bigint unsigned default 0,
  entry_time timestamp  default '0000-00-00 00:00:00',
  author_name varchar(64) character set latin1  default '',
  comment_data TEXT character set latin1  default '',
  internal_downtime_id bigint unsigned default 0,
  triggered_by_id bigint unsigned default 0,
  is_fixed smallint default 0,
  duration bigint(20) default 0,
  scheduled_start_time timestamp  default '0000-00-00 00:00:00',
  scheduled_end_time timestamp  default '0000-00-00 00:00:00',
  was_started smallint default 0,
  actual_start_time timestamp  default '0000-00-00 00:00:00',
  actual_start_time_usec  int default 0,
  is_in_effect smallint default 0,
  trigger_time timestamp  default '0000-00-00 00:00:00',
  PRIMARY KEY  (scheduleddowntime_id),
  UNIQUE KEY instance_id (instance_id,object_id,entry_time,internal_downtime_id)
) ENGINE=InnoDB COMMENT='Current scheduled host and service downtime';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicechecks
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}servicechecks (
  servicecheck_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  service_object_id bigint unsigned default 0,
  check_type smallint default 0,
  current_check_attempt smallint default 0,
  max_check_attempts smallint default 0,
  state smallint default 0,
  state_type smallint default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  command_object_id bigint unsigned default 0,
  command_args TEXT character set latin1  default '',
  command_line TEXT character set latin1  default '',
  timeout smallint default 0,
  early_timeout smallint default 0,
  execution_time double  default '0',
  latency double  default '0',
  return_code smallint default 0,
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  perfdata TEXT character set latin1  default '',
  PRIMARY KEY  (servicecheck_id)
) ENGINE=InnoDB  COMMENT='Historical service checks';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicedependencies
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}servicedependencies (
  servicedependency_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  service_object_id bigint unsigned default 0,
  dependent_service_object_id bigint unsigned default 0,
  dependency_type smallint default 0,
  inherits_parent smallint default 0,
  timeperiod_object_id bigint unsigned default 0,
  fail_on_ok smallint default 0,
  fail_on_warning smallint default 0,
  fail_on_unknown smallint default 0,
  fail_on_critical smallint default 0,
  PRIMARY KEY  (servicedependency_id),
  UNIQUE KEY instance_id (instance_id,config_type,service_object_id,dependent_service_object_id,dependency_type,inherits_parent,fail_on_ok,fail_on_warning,fail_on_unknown,fail_on_critical)
) ENGINE=InnoDB COMMENT='Service dependency definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}serviceescalations
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}serviceescalations (
  serviceescalation_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  service_object_id bigint unsigned default 0,
  timeperiod_object_id bigint unsigned default 0,
  first_notification smallint default 0,
  last_notification smallint default 0,
  notification_interval double  default '0',
  escalate_on_recovery smallint default 0,
  escalate_on_warning smallint default 0,
  escalate_on_unknown smallint default 0,
  escalate_on_critical smallint default 0,
  PRIMARY KEY  (serviceescalation_id),
  UNIQUE KEY instance_id (instance_id,config_type,service_object_id,timeperiod_object_id,first_notification,last_notification)
) ENGINE=InnoDB  COMMENT='Service escalation definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}serviceescalation_contactgroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}serviceescalation_contactgroups (
  serviceescalation_contactgroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  serviceescalation_id bigint unsigned default 0,
  contactgroup_object_id bigint unsigned default 0,
  PRIMARY KEY  (serviceescalation_contactgroup_id),
  UNIQUE KEY instance_id (serviceescalation_id,contactgroup_object_id)
) ENGINE=InnoDB  COMMENT='Service escalation contact groups';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}serviceescalation_contacts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}serviceescalation_contacts (
  serviceescalation_contact_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  serviceescalation_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  PRIMARY KEY  (serviceescalation_contact_id),
  UNIQUE KEY instance_id (instance_id,serviceescalation_id,contact_object_id)
) ENGINE=InnoDB  COMMENT='Service escalation contacts';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicegroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}servicegroups (
  servicegroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  servicegroup_object_id bigint unsigned default 0,
  alias TEXT character set latin1  default '',
  PRIMARY KEY  (servicegroup_id),
  UNIQUE KEY instance_id (instance_id,config_type,servicegroup_object_id)
) ENGINE=InnoDB  COMMENT='Servicegroup definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicegroup_members
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}servicegroup_members (
  servicegroup_member_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  servicegroup_id bigint unsigned default 0,
  service_object_id bigint unsigned default 0,
  PRIMARY KEY  (servicegroup_member_id)
) ENGINE=InnoDB  COMMENT='Servicegroup members';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}services
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}services (
  service_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  host_object_id bigint unsigned default 0,
  service_object_id bigint unsigned default 0,
  display_name varchar(255) character set latin1 collate latin1_general_cs  default '',
  check_command_object_id bigint unsigned default 0,
  check_command_args TEXT character set latin1  default '',
  eventhandler_command_object_id bigint unsigned default 0,
  eventhandler_command_args TEXT character set latin1  default '',
  notification_timeperiod_object_id bigint unsigned default 0,
  check_timeperiod_object_id bigint unsigned default 0,
  failure_prediction_options varchar(64) character set latin1  default '',
  check_interval double  default '0',
  retry_interval double  default '0',
  max_check_attempts smallint default 0,
  first_notification_delay double  default '0',
  notification_interval double  default '0',
  notify_on_warning smallint default 0,
  notify_on_unknown smallint default 0,
  notify_on_critical smallint default 0,
  notify_on_recovery smallint default 0,
  notify_on_flapping smallint default 0,
  notify_on_downtime smallint default 0,
  stalk_on_ok smallint default 0,
  stalk_on_warning smallint default 0,
  stalk_on_unknown smallint default 0,
  stalk_on_critical smallint default 0,
  is_volatile smallint default 0,
  flap_detection_enabled smallint default 0,
  flap_detection_on_ok smallint default 0,
  flap_detection_on_warning smallint default 0,
  flap_detection_on_unknown smallint default 0,
  flap_detection_on_critical smallint default 0,
  low_flap_threshold double  default '0',
  high_flap_threshold double  default '0',
  process_performance_data smallint default 0,
  freshness_checks_enabled smallint default 0,
  freshness_threshold smallint default 0,
  passive_checks_enabled smallint default 0,
  event_handler_enabled smallint default 0,
  active_checks_enabled smallint default 0,
  retain_status_information smallint default 0,
  retain_nonstatus_information smallint default 0,
  notifications_enabled smallint default 0,
  obsess_over_service smallint default 0,
  failure_prediction_enabled smallint default 0,
  notes TEXT character set latin1  default '',
  notes_url TEXT character set latin1  default '',
  action_url TEXT character set latin1  default '',
  icon_image TEXT character set latin1  default '',
  icon_image_alt TEXT character set latin1  default '',
  PRIMARY KEY  (service_id),
  UNIQUE KEY instance_id (instance_id,config_type,service_object_id),
  KEY service_object_id (service_object_id)
) ENGINE=InnoDB  COMMENT='Service definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}servicestatus
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}servicestatus (
  servicestatus_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  service_object_id bigint unsigned default 0,
  status_update_time timestamp  default '0000-00-00 00:00:00',
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  perfdata TEXT character set latin1  default '',
  check_source TEXT character set latin1  default '',
  current_state smallint default 0,
  has_been_checked smallint default 0,
  should_be_scheduled smallint default 0,
  current_check_attempt smallint default 0,
  max_check_attempts smallint default 0,
  last_check timestamp  default '0000-00-00 00:00:00',
  next_check timestamp  default '0000-00-00 00:00:00',
  check_type smallint default 0,
  last_state_change timestamp  default '0000-00-00 00:00:00',
  last_hard_state_change timestamp  default '0000-00-00 00:00:00',
  last_hard_state smallint default 0,
  last_time_ok timestamp  default '0000-00-00 00:00:00',
  last_time_warning timestamp  default '0000-00-00 00:00:00',
  last_time_unknown timestamp  default '0000-00-00 00:00:00',
  last_time_critical timestamp  default '0000-00-00 00:00:00',
  state_type smallint default 0,
  last_notification timestamp  default '0000-00-00 00:00:00',
  next_notification timestamp  default '0000-00-00 00:00:00',
  no_more_notifications smallint default 0,
  notifications_enabled smallint default 0,
  problem_has_been_acknowledged smallint default 0,
  acknowledgement_type smallint default 0,
  current_notification_number smallint default 0,
  passive_checks_enabled smallint default 0,
  active_checks_enabled smallint default 0,
  event_handler_enabled smallint default 0,
  flap_detection_enabled smallint default 0,
  is_flapping smallint default 0,
  percent_state_change double  default '0',
  latency double  default '0',
  execution_time double  default '0',
  scheduled_downtime_depth smallint default 0,
  failure_prediction_enabled smallint default 0,
  process_performance_data smallint default 0,
  obsess_over_service smallint default 0,
  modified_service_attributes  int default 0,
  event_handler TEXT character set latin1  default '',
  check_command TEXT character set latin1  default '',
  normal_check_interval double  default '0',
  retry_check_interval double  default '0',
  check_timeperiod_object_id bigint unsigned default 0,
  PRIMARY KEY  (servicestatus_id),
  UNIQUE KEY object_id (service_object_id)
) ENGINE=InnoDB  COMMENT='Current service status information';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}service_contactgroups
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}service_contactgroups (
  service_contactgroup_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  service_id bigint unsigned default 0,
  contactgroup_object_id bigint unsigned default 0,
  PRIMARY KEY  (service_contactgroup_id)
) ENGINE=InnoDB  COMMENT='Service contact groups';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}service_contacts
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}service_contacts (
  service_contact_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  service_id bigint unsigned default 0,
  contact_object_id bigint unsigned default 0,
  PRIMARY KEY  (service_contact_id)
) ENGINE=InnoDB  COMMENT='Service contacts';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}statehistory
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}statehistory (
  statehistory_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  state_time timestamp  default '0000-00-00 00:00:00',
  state_time_usec  int default 0,
  object_id bigint unsigned default 0,
  state_change smallint default 0,
  state smallint default 0,
  state_type smallint default 0,
  current_check_attempt smallint default 0,
  max_check_attempts smallint default 0,
  last_state smallint default 0,
  last_hard_state smallint default 0,
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  PRIMARY KEY  (statehistory_id)
) ENGINE=InnoDB COMMENT='Historical host and service state changes';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}systemcommands
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}systemcommands (
  systemcommand_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  start_time timestamp  default '0000-00-00 00:00:00',
  start_time_usec  int default 0,
  end_time timestamp  default '0000-00-00 00:00:00',
  end_time_usec  int default 0,
  command_line TEXT character set latin1  default '',
  timeout smallint default 0,
  early_timeout smallint default 0,
  execution_time double  default '0',
  return_code smallint default 0,
  output TEXT character set latin1  default '',
  long_output TEXT  default '',
  PRIMARY KEY  (systemcommand_id),
  UNIQUE KEY instance_id (instance_id,start_time,start_time_usec)
) ENGINE=InnoDB  COMMENT='Historical system commands that are executed';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}timeperiods
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}timeperiods (
  timeperiod_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  config_type smallint default 0,
  timeperiod_object_id bigint unsigned default 0,
  alias TEXT character set latin1  default '',
  PRIMARY KEY  (timeperiod_id),
  UNIQUE KEY instance_id (instance_id,config_type,timeperiod_object_id)
) ENGINE=InnoDB  COMMENT='Timeperiod definitions';

-- --------------------------------------------------------

--
-- Table structure for table {{data.modules.ido2db.database.prefix}}timeperiod_timeranges
--

CREATE TABLE IF NOT EXISTS {{data.modules.ido2db.database.prefix}}timeperiod_timeranges (
  timeperiod_timerange_id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  instance_id bigint unsigned default 0,
  timeperiod_id bigint unsigned default 0,
  day smallint default 0,
  start_sec  int default 0,
  end_sec  int default 0,
  PRIMARY KEY  (timeperiod_timerange_id)
) ENGINE=InnoDB  COMMENT='Timeperiod definitions';


-- -----------------------------------------
-- add index (delete)
-- -----------------------------------------

-- for periodic delete 
-- instance_id and
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

-- servicestatus
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
CREATE INDEX loge_inst_id_time_idx on {{data.modules.ido2db.database.prefix}}logentries (instance_id ASC, logentry_time DESC);

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

-- statehistory
CREATE INDEX statehist_i_id_o_id_s_ty_s_ti on {{data.modules.ido2db.database.prefix}}statehistory(instance_id, object_id, state_type, state_time);
--#2274
create index statehist_state_idx on {{data.modules.ido2db.database.prefix}}statehistory(object_id,state);


-- Icinga Web Notifications
CREATE INDEX notification_idx ON {{data.modules.ido2db.database.prefix}}notifications(notification_type, object_id, start_time);
CREATE INDEX notification_object_id_idx ON {{data.modules.ido2db.database.prefix}}notifications(object_id);
CREATE INDEX contact_notification_idx ON {{data.modules.ido2db.database.prefix}}contactnotifications(notification_id, contact_object_id);
CREATE INDEX contacts_object_id_idx ON {{data.modules.ido2db.database.prefix}}contacts(contact_object_id);
CREATE INDEX contact_notif_meth_notif_idx ON {{data.modules.ido2db.database.prefix}}contactnotificationmethods(contactnotification_id, command_object_id);
CREATE INDEX command_object_idx ON {{data.modules.ido2db.database.prefix}}commands(object_id); 
CREATE INDEX services_combined_object_idx ON {{data.modules.ido2db.database.prefix}}services(service_object_id, host_object_id);


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
INSERT INTO {{data.modules.ido2db.database.prefix}}dbversion (name, version, create_time, modify_time) VALUES ('idoutils', '1.10.0', NOW(), NOW()) ON DUPLICATE KEY UPDATE version='1.10.0', modify_time=NOW();


