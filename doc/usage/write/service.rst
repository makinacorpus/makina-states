Write a new makina-state service
================================




14:40 <kiorky> jessaye de comprendre ce que jai voulu faire en fait avec la liste allowed_ips
14:40 <kiorky> mais je pense qu'en fait elle sert plus car jai voulu faire des restrictions plus fines apres
14:41 <kiorky> oui cest pas bon
14:41 <kiorky> je corrige.
14:42 <kiorky> ca revient au meme dans ce qui est rendu mais le pillar aura pas de repetition.
14:44 <kiorky> tu peux regarder la difference;
14:45 <kiorky> mastersalt '*'  state.sls makina-states.services.firewall.shorewall
14:45 <kiorky> je lai appliqué partout
14:48 <kiorky> pour snmp, il faut que je finisshe lintegration lxc/saltcloud avant, faut que jarrete de forker sinon je finis pas
14:48 <kiorky> mais tu peux aussi lecrire et j'en ferais la review.
14:48 <kiorky> je n'ai pas dis le contraire, mais je suis tout seul ;)
14:49 <kiorky> et ma tache actuelle cest de finir saltcloud/lxc car jai le deploiement nmd
14:49 <kiorky> a faire
14:49 <kiorky> sur lequel tu peux appliquer quoi?
14:50 <kiorky> c'est un service donc tu peux regarder tout ce qu'il y a dans services
14:50 <kiorky> et il va donc dans la catégorie monitoring
14:51 <kiorky> https://github.com/makinacorpus/makina-states/tree/master/services
14:51 <kiorky> https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_circus.py pour les parametres
14:51 <kiorky> (faire un nouveau module 'mc_snmp.py')
14:52 <kiorky> apres, il faut le brancher dans mc_services.py puis dans _macros/services.jinja
14:52 <kiorky> dans mc_services.py il faut rajouter 1. dans settings les settings de mc_snmp 2. lenregistrement de la formula dans registry
14:53 <kiorky> eg pour circus https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_services.py#L111 &
               https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_services.py#L198
14:54 <kiorky> je vois que yann avait oublié la registry
14:54 <kiorky> :)
14:54 <kiorky> (cest de lui le module circus mais je te le prends comme exemple car il est a coté dou va etre snmp)
14:54 <kiorky> je suis en train de te la faire
14:54 <kiorky> tu loggues ta conversation
14:55 <kiorky> pour brancher dans la macro
14:55 <kiorky> exemple:
14:55 <kiorky> https://github.com/makinacorpus/makina-states/blob/master/_macros/services.jinja#L51
14:55 <kiorky> et de la tu peux creer https://github.com/makinacorpus/makina-states/blob/master/services/monitoring/snmp.sls &
               https://github.com/makinacorpus/makina-states/blob/master/services/monitoring/snmp-standalone.sls
14:56 <kiorky> en prenant exemple sur https://github.com/makinacorpus/makina-states/blob/master/services/monitoring/circus.sls &
               https://github.com/makinacorpus/makina-states/blob/master/services/monitoring/circus-standalone.sls



https://wiki.makina-corpus.net/index.php/DevOps:SaltStack
