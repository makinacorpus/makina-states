<?php
// -----------------------------------------------------------------------------
// LOCAL SETTINGS: OVERRIDES OF SETTINGS FROM settings.php and set in DATABASE
// -----------------------------------------------------------------------------
// **************** WWARNING: MANAGED BY SALT *** MANUAL MODIFICATIONS REMOVED
// do your own overrides in a file included at the end of this one (only if 
// present): overrides.settings.php. 
//
//
// -----------------------------------------------------------------------------
// Continuous Integration:
// -----------------------------------------------------------------------------
// Here is a list of feature that may or may not be enabled
//
// example of one variable
//$conf['my_thing_one_enabled'] = false;
// exemple of another
//$conf['my_thing_two_enabled'] = true;
$conf['mc_external_publications_allowed'] = {{ mc_external_publications_allowed }};
// -----------------------------------------------------------------------------


// Do not use the new image style token. it removes images from varnish and 
// breaks some modules
$conf['image_allow_insecure_derivatives'] = {{ image_allow_insecure_derivatives }};

// AVOID SENDING emails if not in production env -------------------------------
$conf['reroute_email_enable'] = {{ reroute_email_enabled }};
$conf['reroute_email_address'] = '{{ reroute_email_address }}';

// BASE URL --------------------------------------------------------------------
$base_url = '{{ base_url }}';
// this is a hack for drush in site-install mode, overriding base_url with crap,
// at least you have a copy in variables, if needed
$conf['base_url'] = $base_url;

// reduce uneeded queries by increasing the allowed max size of cached sentences (default is 75)
$conf['locale_cache_length'] = {{ locale_cache_length }}; //204800;

// Imagecache
$conf['image_jpeg_quality'] = {{ image_jpeg_quality }}; //95;

{% if with_solr %}
// Search Solr  ///////////////////////////////////////////////////////////////
$conf['solr_default_search_server_host'] = "{{ solr_default_search_server_host }}";
$conf['solr_default_search_server_port'] = "{{ solr_default_search_server_port }}";
$conf['solr_default_search_server_path'] = "{{ solr_default_search_server_path }}";
$conf['search_api_attachments_extract_using'] = "solr";
{% endif %}

// CRON ///////////////////////////////////////////////////////////////
// disallow the poor-man cron, we do it via drush
$conf['cron_safe_threshold'] = 0;
// do not limit time for cron tasks
$conf['elysia_cron_time_limit'] = 0;

{% if with_smtp %}
// SMTP ///////////////////////////////////////////////////////////////
$conf['smtp_on'] = 1;
$conf['smtp_host'] = "{{ smtp_host }}";
$conf['smtp_from'] = "{{ smtp_from }}";
$conf['smtp_fromname'] = "{{ smtp_fromname }}";
{% endif %}

{% if $with_simpletest %}
// Simpletest /////////////////////////////////////////////////////////////////
$conf['simpletest_remote_url'] = '{{ base_url }}';
{% endif %}

{% if $with_varnish %}
// Varnish handling ///////////////////////////////////////////////////////////
// Tell Drupal it's behind a proxy
/**
 * Enable this setting to determine the correct IP address of the remote
 * client by examining information stored in the X-Forwarded-For headers.
 * X-Forwarded-For headers are a standard mechanism for identifying client
 * systems connecting through a reverse proxy server, such as Squid or
 * Pound. Reverse proxy servers are often used to enhance the performance
 * of heavily visited sites and may also provide other site caching,
 * security or encryption benefits. If this Drupal installation operates
 * behind a reverse proxy, this setting should be enabled so that correct
 * IP address information is captured in Drupal's session management,
 * logging, statistics and access management systems; if you are unsure
 * about this setting, do not have a reverse proxy, or Drupal operates in
 * a shared hosting environment, this setting should remain commented out.
 */
$conf['reverse_proxy'] = true;

/*
 * When Varnish is used, "page_cache_invoke_hooks" must be set as "false".
 * While static files (JS, CSS, images, etc.) all show the proper cache 
 * lifetime, the nodes themselves will send back "max-age=0", causing a reverse
 * proxy cache miss on eminently-cacheable content.
 * Without the last variable, anonymous users will get nodes/pages with the
 * max-age=0 and the proxy won’t cache it. Setting it to false allows the node
 * to be sent with the max-age set to the cache lifetime set in the admin UI.
 *
 * @see http://drupal.org/node/804864
 */
// Bypass Drupal bootstrap for anonymous users so that Drupal sets max-age=0
// this setting is the old aggressive mode in D6
$conf['page_cache_invoke_hooks'] = {{ page_cache_invoke_hooks }};
$conf['cache'] = {{ cache }}; //should be 1
$conf['block_cache'] = {{ block_cache }}; // should be 1
// this will be in Cache-Control: public max-age
$conf['page_cache_maximum_age'] = {{ page_cache_maximum_age }};
// Define Drupal cache settings:--------------
// inactivate database connection if the cache backend doesn't need it
// (cache_page) if the page is not cached the db connection will be made later
$conf['page_cache_without_database'] = {{ page_cache_without_database }};

/**
 * Set this value if your proxy server sends the client IP in a header other
 * than X-Forwarded-For.
 *
 * The "X-Forwarded-For" header is a comma+space separated list of IP addresses,
 * only the last one (the left-most) will be used.
 */
$conf['reverse_proxy_header'] = 'HTTP_X_FORWARDED_FOR';

/**
 * reverse_proxy accepts an array of IP addresses.
 *
 * Each element of this array is the IP address of any of your reverse
 * proxies. Filling this array Drupal will trust the information stored
 * in the X-Forwarded-For headers only if Remote IP address is one of
 * these, that is the request reaches the web server from one of your
 * reverse proxies. Otherwise, the client could directly connect to
 * your web server spoofing the X-Forwarded-For headers.
 */
$conf['reverse_proxy_addresses'] = {{ varnish_reverse_proxy_addresses }};

/**
 * Page caching:
 *
 * By default, Drupal sends a "Vary: Cookie" HTTP header for anonymous page
 * views. This tells a HTTP proxy that it may return a page from its local
 * cache without contacting the web server, if the user sends the same Cookie
 * header as the user who originally requested the cached page. Without "Vary:
 * Cookie", authenticated users would also be served the anonymous page from
 * the cache. If the site has mostly anonymous users except a few known
 * editors/administrators, the Vary header can be omitted. This allows for
 * better caching in HTTP proxies (including reverse proxies), i.e. even if
 * clients send different cookies, they still get content served from the cache
 * if aggressive caching is enabled and the minimum cache time is non-zero.
 * However, authenticated users should access the site directly (i.e. not use an
 * HTTP proxy, and bypass the reverse proxy if one is used) in order to avoid
 * getting cached pages from the proxy.
 */
$conf['omit_vary_cookie'] = {{ omit_vary_cookie }}; // usually false;

{%   if $with_varnish_module %}
// VARNISH module
$conf['cache_backends'][1] = 'sites/all/modules/varnish/varnish.cache.inc';
$conf['cache_class_cache_page'] = 'VarnishCache';
$conf['varnish_control_terminal'] = '{{ varnish_control_terminal_string }}';
$conf['varnish_cache_clear'] = 0; //0: none 1: drupal defaults
$conf['varnish_flush_cron'] = 0; // no flush of varnish when drupal cron runs (heresy!)
$conf['varnish_socket_timeout'] = {{ varnish_socket_timeout }}; //default is 100-> 100ms; 3000->3s
// see /etc/varnish/secret on the varnish server
$conf['varnish_control_key'] = '{{ varnish_control_key }}';
{%   endif %}
{% endif %}

// This is the minimum cache validity
//$conf['cache_lifetime'] = 10800; // 0 is infinite., 10800->6h
// Broken feature (@Damien Tournoud http://drupal.org/node/1816424#comment-6730222)
// Always put 0
$conf['cache_lifetime'] = 0; // 0 is infinite., 10800->6h
// Also bypass Drupal hardcoded block cache disabled when hook_node_grant
// is implemented by at least one module
// See and apply http://drupal.org/node/1930960#comment-7124130
$conf['block_cache_bypass_node_grants'] = {{ block_cache_bypass_node_grants }}; // usually 1;

// File system ////////////////////////////////////////////////////////////////
// Warning: when PHP-FPM is chrooted, we musn't use real absolute path but only
// "absolute path in the choot"
$conf['file_directory_path'] = 'site/default/files';
{% if chrooted %}
if (!function_exists('drush_main')) {
  $conf['file_private_path'] = '/var/private';
  $conf['file_directory_temp'] = '/var/tmp';
  $conf['file_temporary_path'] = '/var/tmp';
} else {
{% endif %}
  $root = dirname(dirname(dirname(dirname(__FILE__))));
  $conf['file_private_path'] = $root . '/var/private';
  $conf['file_directory_temp'] = $root . '/var/tmp';
  $conf['file_temporary_path'] = $root . '/var/tmp';
{% if chrooted %}
}
{% endif %}

// Cookies and cache //////////////////////////////////////////////////////////
// NO_CACHE cookie on POST (can be used by nginx microcache and Varnish)
// Enter the number of seconds to set a cookie for when a user submits any form
// on the website. This will ensure that any page they see after submitting a
// form will be dynamic and not cached.
$conf['cookie_cache_bypass_adv_cache_lifetime']= {{ cookie_cache_bypass_adv_cache_lifetime }};
// Choose whether or not the cookie will be set for just the path the user is
// viewing when filling out the form, or it it will be set for the entire
// website.
// Please read the Cookie Cache Bypass Advanced module readme beforealtering
// this setting
$conf['cookie_cache_bypass_adv_cookie_path']='entire_site';
// Choose when to set the cache bypass cookie. The safest time is before any
// other validation scripts run, but this may cause people spamming your forms
// to get more non-cached pages than you wish.
// The least aggressive setting is as the last submit function. 
// However this setting may cause the cookie to not be set in some situations.
// ['before_validate','before_submit','after_submit','after_validate']
$conf['cookie_cache_bypass_adv_set_time']='after_validate';

// FORM cache validity (default is 6 hours, several gigbytes of useless cache),
// 1 hour should be enough
$conf['form_cache_retention_time'] = 3600;

// Log level //////////////////////////////////////////////////////////////////
// 1 means some errors get to the end user, 2 means all erros, 0 none.
$conf['error_level'] = {{ error_level }}; 

// Compression ////////////////////////////////////////////////////////////////
$conf['preprocess_css'] = {{ preprocess_css }};
$conf['preprocess_js'] =  {{ preprocess_js }};
// compression is done on nginx/apache level NEVER SET THIS to 1!
$conf['page_compression'] = 0;

// File system permissions ////////////////////////////////////////////////////
// default is 0775, we have user-group:www-data in site/default/files
// when creating a new directory the first '2' will enforce keeping
// user-group as the group of files in this directory, 'others' do
// not need anything, so 2770 is good. But a 1st 0 should be added
// to say it's an octal mode (and do not add quotes)
$conf['file_chmod_directory']=02770;
// default is 0664
$conf['file_chmod_file']=0660;
// ensure nothing in the default multithread shared umask will break
// our mkdir commands (chmod is not impacted, but mkdir is...)
umask(0000);

{% if with_redis %}
// Redis Configuration
define('PREDIS_BASE_PATH','sites/all/libraries/predis/');
$conf['redis_client_interface'] = 'Predis';
$conf['redis_client_host'] = '{{ redis_server }}';
$conf['redis_client_port'] = '{{ redis_port }}';
$conf['redis_client_base'] = {{ redis_base }};
{% endif %}

{% if with_redis_session_proxy %}
// SSO  //////////////////////////////////////////////////////////////////////
// SESSION PROXY: Replace core session management with Session Proxy API.
$conf['session_inc'] = 'sites/all/modules/session_proxy/session.inc';
// SESSION PROXY: activate alternative native session support in Redis
// and prevent internal session managment by Drupal.
//setting this to TRUE will made session proxy using SessionProxy_Backend_Native by default
$conf['session_storage_force_default'] = TRUE;
{% endif %}

{% if with_redis_locks %}
// Redis as Lock Backend
$conf['lock_inc'] = 'sites/all/modules/redis/redis.lock.inc';
{% endif %}

// Caching ////////////////////////////////////////////////////////////////////
// Set domain/subdomain
$cache_domain = $_SERVER['HTTP_HOST'];
require_once DRUPAL_ROOT . '/' . 'includes/cache.inc' ;
$conf['cache_prefix']['default'] = $cache_domain;

// Define cache engines:
//----------------------
// * database, default, is 'DrupalDatabaseCache'
{% if with_file_cache_backend %}
// * filecache drupal7 : 'DrupalFileCache'
$conf['cache_backends'][2] = 'sites/all/modules/filecache/filecache.inc';
{% endif %}
{% if with_memcache_cache_backend %}
// Memcache drupal7 : 'MemCacheDrupal'
$conf['cache_backends'][3] = 'sites/all/modules/memcache/memcache.inc';
{% endif %}
{% if with_mongodb_cache_backend %}
// Mongodb drupal7 : 'DrupalMongoDBCache'
$conf['cache_backends'][4] = 'sites/all/modules/mongodb/mongodb_cache/mongodb_cache.inc';
{% endif %}
{% if with_redis_cache_backend %}
// Redis drupal7 : 'Redis_Cache'
$conf['cache_backends'][5] = 'sites/all/modules/redis/redis.autoload.inc';
{% endif %}
{% if with_apc_cache_backend %}
// APC drupal7 : 'Apc_Cache'
$conf['cache_backends'][6] = 'sites/all/modules/apc/apc_cache.inc';
{% endif %}

{% if cache %}
// Define cache bins
//------------------
//  here's the magic, deporting several cache on the appropriate place
// cache name |  usage/frequency/size (but may depend on your real cache contents, mode brain on)
// default    |  any/any/any          select memcache, apc, file or db
$conf['cache_default_class']          = '{{ cache_bin_default }}';
// WARNING: this one is 'cache_class_cache' and not 'cache_class_cache_cache'
// general    |  all/every/medium     select apc > memcache > file > db
$conf['cache_class_cache']            = '{{ cache_bin_cache }}';
// bootstrap  |  all/every/medium     select apc > db
$conf['cache_class_cache_bootstrap']  = '{{ cache_bin_bootstrap }}';
// block      |  any/often/small      select memcache > db > file
$conf['cache_class_cache_block']      = '{{ cache_bin_block }}';
// field      |  page/some/large      select file > memcache > db
$conf['cache_class_cache_content']    = '{{ cache_bin_content }}';
// filter     |  page/some/large      select file > memcache > db
$conf['cache_class_cache_filter']     = '{{ cache_bin_filter }}';
// form       |  edit/rare/medium     select file > memcache > db
$conf['cache_class_cache_form']       = '{{ cache_bin_form }}';
// menu       |  any/often/large      select memcache > db > file
$conf['cache_class_cache_menu']       = '{{ cache_bin_menu }}';
// page       |  page/often/large     select memcache > file > db
$conf['cache_class_cache_page']       = '{{ cache_bin_page }}';
// session    |  any/any/small        select apc (mono server) > memcache > db
$conf['cache_class_cache_session']    = '{{ cache_bin_session }}';
// update     |  system/rare/large,   select file > db
$conf['cache_class_cache_update']     = '{{ cache_bin_update }}';
// users      |  any/some/large       select memcache > file > db
$conf['cache_class_cache_users']      = '{{ cache_bin_users }}';
// views      |  any/some/large       select memcache > file > db
$conf['cache_class_cache_views']      = '{{ cache_bin_views }}';
// views data |  any/often/small      select apc > db
$conf['cache_class_cache_views_data'] = '{{ cache_bin_views_data }}';
// path
$conf['cache_class_cache_path'] = '{{ cache_bin_path }}';
// tokens
$conf['cache_class_cache_tokens'] = '{{ cache_bin_tokens }}';
// rules
$conf['cache_class_cache_rules'] = '{{ cache_bin_rules }}';
// field
$conf['cache_class_cache_field'] = '{{ cache_bin_field }}';

// EntityCache
$conf['cache_class_cache_entity_comment'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_file'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_node'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_og_membership'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_og_membership_type'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_profile2'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_taxonomy_term'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_taxonomy_vocabulary'] = '{{ cache_bin_entity }}';
$conf['cache_class_cache_entity_user'] = '{{ cache_bin_entity }}';
{% endif %}

$conf['site_mail'] = '{{ site_email }}';

// Pure performance: avoid banned ip query during bootstrap.
$conf['blocked_ips'] = array();

{% if with_local_overrides %}
// Local overrides ////////////////////////////////////////////////////////////
// If you want to alter some default setting, create your
// overrides.settings.php and put theses settings inside like
// ---------- overrides.settings.php ---
// <?php
// My Overrides
//=============================================================
// Overrides for development site (disable all caches).
//$conf['block_cache'] = 0;
//$conf['cache'] = 0; // 0 is no cache mode.
//$conf['preprocess_css'] = 0;
//$conf['preprocess_js'] = 0;
//$conf['omit_vary_cookie'] = false;
//// Default cache class
//$conf['cache_class_cache_page'] = 'DrupalDatabaseCache';
//$conf['error_level'] = 0; // 1 means errors get to the end user.
//$conf['site_mail'] = 'webmaster@example.com';
// -------------------------------------
$overridefile = DRUPAL_ROOT . '/sites/default/overrides.settings.php';
if (file_exists($overridefile)) {
  include_once($overridefile);
}
{% endif %}
