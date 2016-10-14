from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import six
from os import path, walk
import traceback
import re

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native
from ansible.plugins.action import ActionBase
from mc_states.api import magicstring


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def _mutually_exclusive(self):
        dir_arguments = [
            self.source_dir, self.files_matching, self.ignore_files,
            self.depth
        ]
        if self.source_file and None not in dir_arguments:
            err_msg = (
                "Can not include {0} with file argument"
                .format(", ".join(self.VALID_DIR_ARGUMENTS))
            )
            raise AnsibleError(err_msg)
        elif [
            bool(self.content_source),
            bool(self.source_dir),
            bool(self.source_file)
        ].count(True) > 1:
            err_msg = (
                "You must choose between file/dir/<inline_content>"
            )
            raise AnsibleError(err_msg)

    def _set_dir_defaults(self):
        if not self.depth:
            self.depth = 0

        if self.files_matching:
            self.matcher = re.compile(r'{0}'.format(self.files_matching))
        else:
            self.matcher = None

        if not self.ignore_files:
            self.ignore_files = list()

        if isinstance(self.ignore_files, str):
            self.ignore_files = self.ignore_files.split()

        elif isinstance(self.ignore_files, dict):
            return {
                'failed': True,
                'message': '{0} must be a list'.format(self.ignore_files)
            }

    def _set_args(self):
        """ Set instance variables based on the arguments that were passed
        """
        self.VALID_DIR_ARGUMENTS = [
            'dir', 'depth', 'files_matching', 'ignore_files'
        ]
        self.VALID_FILE_ARGUMENTS = ['file', '_raw_params']
        self.GLOBAL_FILE_ARGUMENTS = ['name', 'content']

        self.VALID_ARGUMENTS = (
            self.VALID_DIR_ARGUMENTS + self.VALID_FILE_ARGUMENTS +
            self.GLOBAL_FILE_ARGUMENTS
        )
        for arg in self._task.args:
            if arg not in self.VALID_ARGUMENTS:
                err_msg = '{0} is not a valid option in debug'.format(arg)
                raise AnsibleError(err_msg)

        self.return_results_as_name = self._task.args.get('name', None)
        if self._task._role:
            if not self.return_results_as_name:
                self.return_results_as_name = self._task._role._role_name
        if self.return_results_as_name == '__GLOBAL__':
            self.return_results_as_name = None

        self.content_source = self._task.args.get('content', None)
        self.source_dir = self._task.args.get('dir', None)
        self.source_file = self._task.args.get('file', None)

        try:
            raw_params = self._task.get_ds().get(self._task.action, None)
        except Exception:
            raw_params = None
        if (
            isinstance(raw_params, six.string_types) and
            not self.content_source and
            not self.source_dir and
            not self.source_file
        ):
            if '\n' in raw_params:
                self.content_source = raw_params
            else:
                self.source_file = raw_params
        if (
            not self.content_source and
            not self.source_dir and
            not self.source_file
        ):
            self.source_file = 'main.yml'

        self.depth = self._task.args.get('depth', None)
        self.files_matching = self._task.args.get('files_matching', None)
        self.ignore_files = self._task.args.get('ignore_files', None)

        self._mutually_exclusive()

    def run(self, tmp=None, task_vars=None):
        """
        Load yml files recursively from a directory.
        """
        self.VALID_FILE_EXTENSIONS = ['yaml', 'yml', 'json']
        if not task_vars:
            task_vars = dict()

        self.show_content = True
        self._set_args()
        self._task_vars = task_vars
        if self._task._role:
            self._defaults = self._task._role.get_default_vars(
                dep_chain=self._task.get_dep_chain())
        else:
            self._defaults = {}
        self._task_vars.update(self._defaults)

        results = dict()
        if self.source_dir:
            self._set_dir_defaults()
            self._set_root_dir()
            if path.exists(self.source_dir):
                for root_dir, filenames in self._traverse_dir_depth():
                    failed, err_msg, updated_results = (
                        self._load_files_in_dir(root_dir, filenames)
                    )
                    if not failed:
                        results.update(updated_results)
                    else:
                        break
            else:
                failed = True
                err_msg = (
                    '{0} directory does not exist'.format(self.source_dir)
                )
        elif self.content_source:
            try:
                failed, err_msg, updated_results = (
                    self._load_content(self.content_source)
                )
                if not failed:
                    results.update(updated_results)

            except AnsibleError as e:
                err_msg = to_native(e)
                raise AnsibleError(err_msg)
        else:
            try:
                self.source_file = self._find_needle('jinja_vars', self.source_file)
                failed, err_msg, updated_results = (
                    self._load_files(self.source_file)
                )
                if not failed:
                    results.update(updated_results)

            except AnsibleError as e:
                err_msg = to_native(e)
                raise AnsibleError(err_msg)

        if (
            self.return_results_as_name and
            self.return_results_as_name != '__GLOBAL__'
        ):
            scope = dict()
            scope[self.return_results_as_name] = results
            results = scope

        result = super(ActionModule, self).run(tmp, task_vars)

        if failed:
            result['failed'] = failed
            result['message'] = err_msg

        result['ansible_facts'] = results
        result['_ansible_no_log'] = not self.show_content

        return result

    def _set_root_dir(self):
        if self._task._role:
            if self.source_dir.split('/')[0] == 'jinja_vars':
                path_to_use = (
                    path.join(self._task._role._role_path, self.source_dir)
                )
                if path.exists(path_to_use):
                    self.source_dir = path_to_use
            else:
                path_to_use = (
                    path.join(
                        self._task._role._role_path, 'jinja_vars', self.source_dir
                    )
                )
                self.source_dir = path_to_use
        else:
            current_dir = (
                "/".join(self._task._ds._data_source.split('/')[:-1])
            )
            self.source_dir = path.join(current_dir, self.source_dir)

    def _traverse_dir_depth(self):
        """ Recursively iterate over a directory and sort the files in
            alphabetical order. Do not iterate pass the set depth.
            The default depth is unlimited.
        """
        current_depth = 0
        sorted_walk = list(walk(self.source_dir))
        sorted_walk.sort(key=lambda x: x[0])
        for current_root, current_dir, current_files in sorted_walk:
            current_depth += 1
            if current_depth <= self.depth or self.depth == 0:
                current_files.sort()
                yield (current_root, current_files)
            else:
                break

    def _ignore_file(self, filename):
        """ Return True if a file matches the list of ignore_files.
        Args:
            filename (str): The filename that is being matched against.

        Returns:
            Boolean
        """
        for file_type in self.ignore_files:
            try:
                if re.search(r'{0}$'.format(file_type), filename):
                    return True
            except Exception:
                err_msg = 'Invalid regular expression: {0}'.format(file_type)
                raise AnsibleError(err_msg)
        return False

    def _is_valid_file_ext(self, source_file):
        """ Verify if source file has a valid extension
        Args:
            source_file (str): The full path of source file or source file.

        Returns:
            Bool
        """
        success = False
        file_ext = source_file.split('.')
        if len(file_ext) >= 1:
            if file_ext[-1] in self.VALID_FILE_EXTENSIONS:
                success = True
                return success
        return success

    def _load_files(self, filename):
        """ Loads a file and converts the output into a valid Python dict.
        Args:
            filename (str): The source file.

        Returns:
            Tuple (bool, str, dict)
        """
        if not self._is_valid_file_ext(filename):
            err_msg = (
                '{0} does not have a valid extension: {1}'
                .format(filename, ', '.join(self.VALID_FILE_EXTENSIONS))
            )
            return True, err_msg, {}
        data, show_content = self._loader._get_file_contents(filename)
        self.show_content = show_content
        return self._load_content(data, show_content, filename=filename)

    def _load_content(self, data, show_content=True, filename='<string>'):
        results = dict()
        failed = False
        old_data = None
        err_msg = ''
        try:
            data = magicstring(data)
            if (('{{' in data) or ('{%' in data)):
                while old_data != data:
                    old_data = data
                    data = self._templar.template(data)
                data = self._loader.load(data, show_content)
            else:
                data = self._loader.load(data, show_content)
        except (Exception,) as exc:
            trace = traceback.format_exc()
            failed = True
            print('\nFile: {0}'.format(filename))
            err_msg = (
                '{0} does not render correctly: \n{1}\n{2}\n'
                .format(filename, exc, trace))
            if old_data:
                print('\nOriginal data')
                print(old_data)
            if data and (data != old_data):
                print('\nCurrently Rendered data')
                print(data)
            print('\nError')
            print(err_msg)
            return failed, err_msg, results

        if not data:
            data = dict()
        if not isinstance(data, dict):
            failed = True
            err_msg = (
                '{0} must be stored as a dictionary/hash'
                .format(filename)
            )
        else:
            results.update(data)
        return failed, err_msg, results

    def _load_files_in_dir(self, root_dir, var_files):
        """ Load the found yml files and update/overwrite the dictionary.
        Args:
            root_dir (str): The base directory of the list of files that is being passed.
            var_files: (list): List of files to iterate over and load into a dictionary.

        Returns:
            Tuple (bool, str, dict)
        """
        results = dict()
        failed = False
        err_msg = ''
        for filename in var_files:
            stop_iter = False
            # Never include main.yml from a role, as that is the default included by the role
            if self._task._role:
                if filename == 'main.yml':
                    stop_iter = True
                    continue

            filepath = path.join(root_dir, filename)
            if self.files_matching:
                if not self.matcher.search(filename):
                    stop_iter = True

            if not stop_iter and not failed:
                if path.exists(filepath) and not self._ignore_file(filename):
                    failed, err_msg, loaded_data = self._load_files(filepath)
                    if not failed:
                        results.update(loaded_data)

        return failed, err_msg, results
