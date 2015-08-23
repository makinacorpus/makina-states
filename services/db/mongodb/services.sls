include:
  - makina-states.services.db.mongodb.hooks

makina-mongodb-service:
  service.running:
    - name: mongod
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: mongodb-pre-restart
    - watch_in:
      - mc_proxy: mongodb-post-restart

makina-mongodb-restart-service:
  service.running:
    - name: mongod
    - enable: true
    - watch:
      - mc_proxy: mongodb-pre-hardrestart
    - watch_in:
      - mc_proxy: mongodb-post-hardrestart

