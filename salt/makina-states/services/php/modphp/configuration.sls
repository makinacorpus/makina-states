{#
# mod_php: PHP as an apache module
#
# Makina Corpus mod_php Deployment main state
#
# For usage examples please check the file php_example.sls on this same directory
#
# TODO: review comment
# Preferred way of altering default settings is to set them in the apache Virtualhost
# We do not alter the main php.ini configuration file. This file is including
# php_defaults.jinja, you can reuse phpSettings dictionnary on your managed virtualhost template
# for php default values.
#
# If you want to add some more module include this file and reuse phpSettings.packages
# to find the right one (check php_defaults.jinja mapping)
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#}
{% import "makina-states/services/http/apache/init.sls" as apache with context %}
include:
  - makina-states.services.http.apache
