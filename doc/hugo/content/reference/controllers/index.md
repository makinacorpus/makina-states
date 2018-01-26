---
title: Controllers
tags: [reference, installation]
weight: 4000
menu:
  main:
    parent: reference
    identifier: reference_controllers
---
- controllers states purpose is mainly to check:
   - our bundled salt & ansible binaries are ready for operation
   - the cloned code is up to date and clean
   - If the user selected them:
       - crons are in place
       - install links (``/usr/local/bin``) are present
       - RollingRealse updater crons are in place
