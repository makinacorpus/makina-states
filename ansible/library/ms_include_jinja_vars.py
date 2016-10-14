# -*- mode: python -*-

DOCUMENTATION = '''
---

This is inspired from the include_vars action plugin, and has the same
purpose of loading custom variable on the road.
But it differs these ways:
- You can load inline content via the "content" key
- variable files can be either a jinja template or a
  classical variable name.
- It must live inside a 'jinja_vars' folder next to the playbook or the role.
- Another difference is that the variables are
  automaticly namespaced to the role name when coming from a role.
- You can always specify a namespace via the name argument
- If you want no namespace, then use __GLOBAL__ as the name.
- the variables file argument is not mandatory and defaults to 'main.yml'
'''

EXAMPLES = """
In a Playbook "muche":

    - In playbookfoo.yml:

        - ms_include_jinja_vars: |
                ---
                a: {{1+1}}

    - Will make the variable 'a' available with value 2.


In a Playbook "muche":

    - In playbookfoo.yml:

        - ms_include_jinja_vars:
            content: |
                ---
                a: {{1+1}}

    - Will also make the variable 'a' available with value 2.

In a role "bar":

    - In bar/jinja_vars/foo.yml::

        ---
        a: {{1}}


    - In bar/tasks/main.yml::

        - ms_include_jinja_vars:
            file: foo.yml
            name: foo_vars

    - Will make the 'foo_vars' variable available
      with the value '{'a': 1}'


In a role "foo":

    - 'foo/jinja_vars/main.yml'::

        ---
        a: 1

    - 'foo/tasks/main.yml'::

        - ms_include_jinja_vars: {}

    - Will make the 'foo' available with the value '{'a': 1}'


In a role "moo":

    - 'moo/jinja_vars/main.yml'::

        ---
        a: 1

    - 'moo/tasks/main.yml'::

        - ms_include_jinja_vars:
            name: __GLOBAL__

    - Will make all returned value as global variables,
      so 'a' will resolve to 1.

"""
