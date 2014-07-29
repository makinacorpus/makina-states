<?php
# MANAGED VIA SALT -- DO NOT EDIT
{% set data = salt['mc_utils.json_load'](data) %}

##
## Program: pnp4nagios-0.6.16 , Performance Data Addon for Nagios(r)
## License: GPL
## Copyright (c) 2005-2010 Joerg Linge (http://www.pnp4nagios.org)
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
##
# Credit:  Tobi Oetiker, http://people.ee.ethz.ch/~oetiker/webtools/rrdtool/
#

# URL rewriting is used by default to create friendly URLs. 
# Set this value to '0' if URL rewriting is not available on your system.
#
$conf['use_url_rewriting'] = {{data.config_php.conf.use_url_rewriting}};
#
# Location of rrdtool binary
#
$conf['rrdtool'] = "{{data.config_php.conf.rrdtool}}";
#
# RRDTool image size of graphs
#
$conf['graph_width'] = "{{data.config_php.conf.graph_width}}";
$conf['graph_height'] = "{{data.config_php.conf.graph_height}}";
#
# RRDTool image size of graphs in zoom window
#
$conf['zgraph_width'] = "{{data.config_php.conf.zgraph_width}}";
$conf['zgraph_height'] = "{{data.config_php.conf.zgraph_height}}";
#
# Right zoom box offset.
# rrdtool 1.3.x = 30px 
# rrdtool 1.4.x = 22px
#
$conf['right_zoom_offset'] = {{data.config_php.conf.right_zoom_offset}};

#
# RRDTool image size of PDFs
#
$conf['pdf_width']        = "{{data.config_php.conf.pdf_width}}";
$conf['pdf_height']       = "{{data.config_php.conf.pdf_height}}";
$conf['pdf_page_size']    = "{{data.config_php.conf.pdf_page_size}}";   # A4 or Letter
$conf['pdf_margin_top']   = "{{data.config_php.conf.pdf_margin_top}}";
$conf['pdf_margin_left']  = "{{data.config_php.conf.pdf_margin_left}}";
$conf['pdf_margin_right'] = "{{data.config_php.conf.pdf_margin_right}}";
#
# Additional options for RRDTool
#
# Example: White background and no border
# "--watermark 'Copyright by example.com' --slope-mode --color BACK#FFF --color SHADEA#FFF --color SHADEB#FFF"
#
$conf['graph_opt'] = "{{data.config_php.conf.graph_opt}}";
#
# Additional options for RRDTool used while creating PDFs
#
$conf['pdf_graph_opt'] = "{{data.config_php.conf.pdf_graph_opt}}";
#
# Directory where the RRD Files will be stored
#
$conf['rrdbase'] = "{{data.config_php.conf.rrdbase}}";
#
# Location of "page" configs
#
$conf['page_dir'] = "{{data.config_php.conf.page_dir}}";
#
# Site refresh time in seconds
#
$conf['refresh'] = "{{data.config_php.conf.refresh}}";
#
# Max age for RRD files in seconds
# 
$conf['max_age'] = {{data.config_php.conf.max_age}};   
#
# Directory for temporary files used for PDF creation 
#
$conf['temp'] = "{{data.config_php.conf.temp}}";
#
# Link back to Nagios or Thruk ( www.thruk.org ) 
#
$conf['nagios_base'] = "{{data.config_php.conf.nagios_base}}";

#
# Link back to check_mk´s multisite ( http://mathias-kettner.de/checkmk_multisite.html )
#
$conf['multisite_base_url'] = "{{data.config_php.conf.multisite_base_url}}";
#
# Multisite Site ID this PNP installation is linked to
# This is the same value as defined in etc/multisite.mk
#
$conf['multisite_site'] = "{{data.config_php.conf.multisite_site}}";

#
# check authorization against mk_livestatus API 
# Available since 0.6.10
#
$conf['auth_enabled'] = {{data.config_php.conf.auth_enabled}};

#
# Livestatus socket path
# 
#$conf['livestatus_socket'] = "tcp:localhost:6557";
$conf['livestatus_socket'] = "{{data.config_php.conf.livestatus_socket}}";

#
# Which user is allowed to see all services or all hosts?
# Keywords: <USERNAME>
# Example: conf['allowed_for_all_services'] = "nagiosadmin,operator";
# This option is used while $conf['auth_enabled'] = TRUE
$conf['allowed_for_all_services'] = "{{data.config_php.conf.allowed_for_all_services}}";
$conf['allowed_for_all_hosts'] = "{{data.config_php.conf.allowed_for_all_hosts}}";

# Which user is allowed to see additional service links ?
# Keywords: EVERYONE NONE <USERNAME>
# Example: conf['allowed_for_service_links'] = "nagiosadmin,operator";
# 
$conf['allowed_for_service_links'] = "{{data.config_php.conf.allowed_for_service_links}}";

#
# Who can use the host search function ?
# Keywords: EVERYONE NONE <USERNAME>
#
$conf['allowed_for_host_search'] = "{{data.config_php.conf.allowed_for_host_search}}";

#
# Who can use the host overview ?
# This function is called if no Service Description is given.  
#
$conf['allowed_for_host_overview'] = "{{data.config_php.conf.allowed_for_host_overview}}";

#
# Who can use the Pages function?
# Keywords: EVERYONE NONE <USERNAME>
# Example: conf['allowed_for_pages'] = "nagiosadmin,operator";
#
$conf['allowed_for_pages'] = "{{data.config_php.conf.allowed_for_pages}}";

#
# Which timerange should be used for the host overview site ? 
# use a key from array $views[]
#
$conf['overview-range'] = {{data.config_php.conf.overview_range}} ;

#
# Scale the preview images used in /popup 
#
$conf['popup-width'] = "{{data.config_php.conf.popup_width}}";

#
# jQuery UI Theme
# http://jqueryui.com/themeroller/
# Possible values are: lightness, smoothness, redmond, multisite
$conf['ui-theme'] = '{{data.config_php.conf.ui_theme}}';

# Language definitions to use.
# valid options are en_US, de_DE, es_ES, ru_RU, fr_FR 
#
$conf['lang'] = "{{data.config_php.conf.lang}}";

#
# Date format
#
$conf['date_fmt'] = "{{data.config_php.conf.date_fmt}}";

#
# This option breaks down the template name based on _ and then starts to 
# build it up and check the different template directories for a suitable template.
#
# Example:
#
# Template to be used: check_esx3_host_net_usage you create a check_esx3.php
#
# It will find and match on check_esx3 first in templates dir then in templates.dist
#
$conf['enable_recursive_template_search'] = {{data.config_php.conf.enable_recursive_template_search}};

#
# Direct link to the raw XML file.
#
$conf['show_xml_icon'] = {{data.config_php.conf.show_xml_icon}};

#
# Use FPDF Lib for PDF creation ?
#
$conf['use_fpdf'] = {{data.config_php.conf.use_fpdf}};

#
# Use this file as PDF background.
#
$conf['background_pdf'] = "{{data.config_php.conf.background_pdf}}" ;

#
# Enable Calendar
#
$conf['use_calendar'] = {{data.config_php.conf.use_calendar}};

#
# Define default views with title and start timerange in seconds 
#
# remarks: required escape on " with backslash
#
#$views[] = array('title' => 'One Hour',  'start' => (60*60) );

{% for title,view in data.config_php.views.items() %}
$views[] = array(
 'title' => '{{title}}',
 {% for key,value in view.items() %}
 '{{key}}' => {{value}},
 {% endfor %}
);
{% endfor %}

#
# rrdcached support
# Use only with rrdtool svn revision 1511+
#
# $conf['RRD_DAEMON_OPTS'] = 'unix:/tmp/rrdcached.sock';
$conf['RRD_DAEMON_OPTS'] = "{{data.config_php.conf.RRD_DAEMON_OPTS}}";

# A list of directories to search for templates
# /usr/share/pnp4nagios/html/templates.dist is always the last directory to be searched for templates
#
# Add your own template directories here
# First match wins!
#$conf['template_dirs'][] = '/usr/local/check_mk/pnp-templates';

{% for template in data.config_php.conf.template_dirs %}
$conf['template_dirs'][] = "{{template}}";
{% endfor %}

$templates_d = glob("/etc/pnp4nagios/templates.d/*", GLOB_ONLYDIR);
if (is_array($templates_d) && (count($templates_d) > 0)) {
	foreach ($templates_d as $dirname) {
		$conf['template_dirs'][] = "$dirname";
	}
}

#
# Directory to search for special templates
#
$conf['special_template_dir'] = "{{data.config_php.conf.special_template_dir}}";

#
# Regex to detect mobile devices
# This regex is evaluated against the USER_AGENT String
#
$conf['mobile_devices'] = "{{data.config_php.conf.mobile_device}}";
?>
