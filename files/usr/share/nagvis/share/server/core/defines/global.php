<?PHP
/* MANAGED VIA SALT -- DO NOT EDIT */
{% set data = salt['mc_utils.json_load'](data) %}

/*****************************************************************************
 *
 * global.php - File for global constants and some other standards
 *
 * Copyright (c) 2004-2011 NagVis Project (Contact: info@nagvis.org)
 *
 * License:
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 *
 *****************************************************************************/
 
/**
 * @author	Lars Michelsen <lars@vertical-visions.de>
 */

// NagVis Version
define('CONST_VERSION', '{{data.global_php.CONST_VERSION}}');

// Set PHP error handling to standard level
// Different levels for php versions below 5.1 because PHP 5.1 reports
// some annoying strict messages which are OK for us. From version 5.2
// everything is OK when using E_STRICT.
if(version_compare(PHP_VERSION, '5.2') >= 0)
	error_reporting(E_ALL ^ E_STRICT);
else
	error_reporting(E_ALL);

/**
 * Set the search path for included files
 */
set_include_path(
	get_include_path()
	.PATH_SEPARATOR.'../../server/core/classes'
	.PATH_SEPARATOR.'../../server/core/classes/objects'
	.PATH_SEPARATOR.'../../server/core/ext/php-gettext-1.0.9'
);

// Enable/Disable profiling of NagVis using xhprof.  To make use of this the
// xhprof php module needs to be loaded and the xhprof_lib directory needs
// to be available in /var/www.
define('PROFILE', {{data.global_php.PROFILE}});

// enable/disable the debug mode
define('DEBUG', {{data.global_php.DEBUG}});

/**
 * For desired debug output add these possible values:
 * 1: function start and end
 * 2: progress information in the functions
 * 4: render time
 */
define('DEBUGLEVEL', {{data.global_php.DEBUGLEVEL}});

// Path to the debug file
define('DEBUGFILE', '{{data.global_php.DEBUGFILE}}');

// It is possible to define a conf.d directory for splitting the main
// configuration in several files. Only the values defined in the CONST_MAINCFG
// file are editable via the web GUI.
//
// The parameters are applied in this direction:
// 1. hardcoded
// 2. CONST_MAINCFG_DIR
// 3. CONST_MAINCFG
//
// The last value wins.
//
// Path to the main configuration file
define('CONST_MAINCFG', '{{data.global_php.CONST_MAINCFG}}');
define('CONST_MAINCFG_CACHE', '{{data.global_php.CONST_MAINCFG_CACHE}}');

// Path to the main configuration conf.d directory
define('CONST_MAINCFG_DIR', '{{data.global_php.CONST_MAINCFG_DIR}}');

// The directory below the NagVis root which is shared by the webserver
define('HTDOCS_DIR', '{{data.global_php.HTDOCS_DIR}}');

// Needed minimal PHP version
define('CONST_NEEDED_PHP_VERSION', '{{data.global_php.CONST_NEEDED_PHP_VERSION}}');

// NagVis session name
define('SESSION_NAME', '{{data.global_php.SESSION_NAME}}');

// Other basic constants
define('REQUIRES_AUTHORISATION', {{data.global_php.REQUIRES_AUTHORISATION}});
define('GET_STATE', {{data.global_php.GET_STATE}});
define('GET_PHYSICAL_PATH', {{data.global_php.GET_PHYSICAL_PATH}});
define('DONT_GET_OBJECT_STATE', {{data.global_php.DONT_GET_OBJECT_STATE}});
define('DONT_GET_SINGLE_MEMBER_STATES', {{data.global_php.DONT_GET_SINGLE_MEMBER_STATES}});
define('GET_SINGLE_MEMBER_STATES', {{data.global_php.GET_SINGLE_MEMBER_STATES}});
define('HANDLE_USERCFG', {{data.global_php.HANDLE_USERCFG}});
define('ONLY_USERCFG', {{data.global_php.ONLY_USERCFG}});

define('ONLY_STATE', {{data.global_php.ONLY_STATE}});
define('COMPLETE', {{data.global_php.COMPLETE}});

define('IS_VIEW', {{data.global_php.IS_VIEW}});
define('ONLY_GLOBAL', {{data.global_php.ONLY_GLOBAL}});
define('GET_CHILDS', {{data.global_php.GET_CHILDS}});
define('SET_KEYS', {{data.global_php.SET_KEYS}});
define('SUMMARY_STATE', {{data.global_php.SUMMARY_STATE}});
define('COUNT_QUERY', {{data.global_php.COUNT_QUERY}});
define('MEMBER_QUERY', {{data.global_php.MEMBER_QUERY}});
define('HOST_QUERY', {{data.global_php.HOST_QUERY}});

// Maximum length for usernames/passwords
define('AUTH_MAX_PASSWORD_LENGTH', {{data.global_php.AUTH_MAX_PASSWORD_LENGTH}});
define('AUTH_MAX_USERNAME_LENGTH', {{data.global_php.AUTH_MAX_USERNAME_LENGTH}});
define('AUTH_MAX_ROLENAME_LENGTH', {{data.global_php.AUTH_MAX_ROLENAME_LENGTH}});

// Permission wildcard
define('AUTH_PERMISSION_WILDCARD', '{{data.global_php.AUTH_PERMISSION_WILDCARD}}');

// This is being used when logging in using LogonEnv for trusting the given user
define('AUTH_TRUST_USERNAME', {{data.global_php.AUTH_TRUST_USERNAME}});
define('AUTH_NOT_TRUST_USERNAME', {{data.global_php.AUTH_NOT_TRUST_USERNAME}});

// Salt for the password hashes
// Note: If you change this you will need to rehash all saved 
//       password hashes
define('AUTH_PASSWORD_SALT', '{{data.global_php.AUTH_PASSWORD_SALT}}');
?>
