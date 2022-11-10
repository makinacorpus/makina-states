{{ salt['mc_macros.register']('localsettings', 'editor') }}
{% set data = salt['mc_editor.settings']() %}
include:
  - makina-states.localsettings.editor.hooks
editor-alternatives:
  cmd.run:
    - name: "update-alternatives --set editor {{data.editor}} && echo 'changed=false'"
    - stateful: true
    - onlyif: |
       test "x$(update-alternatives --query editor|grep Value|awk '{print $2}')" != "x{{data.editor}}"
    - watch:
      - mc_proxy: editor-pre-install
    - watch_in:
      - mc_proxy: editor-post-install
