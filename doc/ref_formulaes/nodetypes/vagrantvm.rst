Vagrant VM nodetype
=========================
Will trigger some extra setup when we are on a vagrant box.
It already inherit the setup from devhost.

On a vagrant box, we include the docker and lxc states, we also automaticly add
some scripts to manage freespace (zerofree & system-cleanup)

We disable plymouth on ubuntu.

We also manage an **/etc/devhosts** file which is then merged via the provision
script up to the host **/etc/hosts** file to provide access via name to the
machine services.

Thus you can do **http://devhost[NUM].local** in your browser.




