# -*- coding: utf-8 -*-
'''
mc_git / Interaction with Git repositories
===========================================



The difference or to be more precise, the only addition of using
git.latest is that we do a merge --ff-only when pulling in case
of errors to be a bit more fairful on updates

.. code-block:: yaml

    https://github.com/saltstack/salt.git:
      mc_git.latest:
        - rev: develop
        - target: /tmp/salt
'''

# Import python libs
import logging
import os

# Import salt libs
import salt.utils

from salt.states import git

_fail = git._fail
_neutral_test = git._neutral_test

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load if git is available
    '''
    return 'mc_git' if __salt__['cmd.has_exec']('git') else False


def _run_check(*args, **check_cmd_opts):
    """
    Execute the check_cmd logic.

    Return a result dict if ``check_cmd`` succeeds (check_cmd == 0)
    otherwise return True
    """

    cret = __salt__["cmd.run_all"](*args, **check_cmd_opts)
    if cret["retcode"] != 0:
        ret = {
            "comment": "check_cmd execution failed",
            "skip_watch": True,
            "result": False,
        }

        if cret.get("stdout"):
            ret["comment"] += "\n" + cret["stdout"]
        if cret.get("stderr"):
            ret["comment"] += "\n" + cret["stderr"]
        return ret
    # No reason to stop, return True
    return True


def old_latest(name,
           rev=None,
           target=None,
           runas=None,
           user=None,
           force=None,
           force_checkout=False,
           submodules=False,
           mirror=False,
           bare=False,
           remote_name='origin',
           always_fetch=False,
           identity=None,
           onlyif=False,
           unless=False,
           firstrun=True):
    '''
    Make sure the repository is cloned to the given directory and is up to date
    Thin wrapper to git.latest that also makes
    a git merge --only-ff to merge unharmful commits
    without failling hard

    name
        Address of the remote repository as passed to "git clone"

    rev
        The remote branch, tag, or revision ID to checkout after
        clone / before update

    target
        Name of the target directory where repository is about to be cloned

    runas
        Name of the user performing repository management operations

        .. deprecated:: 0.17.0

    user
        Name of the user performing repository management operations

        .. versionadded:: 0.17.0

    force
        Force git to clone into pre-existing directories (deletes contents)

    force_checkout
        Force a checkout even if there might be overwritten changes
        (Default: False)

    submodules
        Update submodules on clone or branch change (Default: False)

    mirror
        True if the repository is to be a mirror of the remote repository.
        This implies bare, and thus is incompatible with rev.

    bare
        True if the repository is to be a bare clone of the remote repository.
        This is incompatible with rev, as nothing will be checked out.

    remote_name
        defines a different remote name.
        For the first clone the given name is set to the default remote,
        else it is just a additional remote. (Default: 'origin')

    always_fetch
        If a tag or branch name is used as the rev a fetch will not occur
        until the tag or branch name changes. Setting this to true will force
        a fetch to occur. Only applies when rev is set. (Default: False)

    identity
        A path to a private key to use over SSH

    onlyif
        A command to run as a check, run the named command only if the command
        passed to the ``onlyif`` option returns true

    unless
        A command to run as a check, only run the named command if the command
        passed to the ``unless`` option returns false
    '''
    ret = {'name': name, 'result': True, 'comment': '', 'changes': {}}

    # Check to make sure rev and mirror/bare are not both in use
    if rev and (mirror or bare):
        return _fail(ret, ('"rev" is not compatible with the "mirror" and '
                           '"bare" arguments'))

    if not target:
        return _fail(ret, '"target" option is required')
    if user is not None and runas is not None:
        # user wins over runas but let warn about the deprecation.
        ret.setdefault('warnings', []).append(
            'Passed both the \'runas\' and \'user\' arguments. Please don\'t. '
            '\'runas\' is being ignored in favor of \'user\'.'
        )
        runas = None
    elif runas is not None:
        # Support old runas usage
        user = runas
        runas = None

    run_check_cmd_kwargs = {'runas': user}

    # check if git.latest should be applied
    cret = _run_check(
        run_check_cmd_kwargs, onlyif, unless
    )
    if isinstance(cret, dict):
        ret.update(cret)
        return ret

    bare = bare or mirror
    check = 'refs' if bare else '.git'

    if os.path.isdir(target) and os.path.isdir('{0}/{1}'.format(target,
                                                                check)):
        # git pull is probably required
        log.debug(('target {0} is found, "git pull" '
                   'is probably required'.format(target)))
        try:
            current_rev = __salt__['git.revision'](target, user=user)

            # handle the case where a branch was provided for rev
            remote_rev = None
            branch = __salt__['git.current_branch'](target, user=user)
            # We're only interested in the remote branch if a branch
            # (instead of a hash, for example) was provided for rev.
            if len(branch) > 0 and branch == rev:
                remote_rev = __salt__['git.ls_remote'](target,
                                                       repository=name,
                                                       branch=branch, user=user,
                                                       identity=identity)

            # only do something, if the specified rev differs from the
            # current_rev and remote_rev
            if current_rev in [rev, remote_rev]:
                new_rev = current_rev
            else:

                if __opts__['test']:
                    return _neutral_test(
                        ret,
                        ('Repository {0} update is probably required (current '
                         'revision is {1})').format(target, current_rev))

                # if remote_name is defined set fetch_opts to remote_name
                if remote_name != 'origin':
                    fetch_opts = remote_name
                else:
                    fetch_opts = ''

                # check remote if fetch_url not == name set it
                remote = __salt__['git.remote_get'](target,
                                                    remote=remote_name,
                                                    user=user)
                if remote is None or remote[0] != name:
                    __salt__['git.remote_set'](target,
                                               remote=remote_name,
                                               url=name,
                                               user=user)
                    ret['changes']['remote/{0}'.format(remote_name)] = "{0} => {1}".format(str(remote), name)

                # caheck if rev is already present in repo, git-fetch otherwise
                if bare:
                    __salt__['git.fetch'](target,
                                          opts=fetch_opts,
                                          user=user,
                                          identity=identity)
                elif rev:

                    cmd = "git rev-parse " + rev + '^{commit}'
                    retcode = __salt__['cmd.retcode'](cmd,
                                                      cwd=target,
                                                      user=user)
                    # there is a issues #3938 addressing this
                    if 0 != retcode or always_fetch:
                        __salt__['git.fetch'](target,
                                              opts=fetch_opts,
                                              user=user,
                                              identity=identity)

                    __salt__['git.checkout'](target,
                                             rev,
                                             force=force_checkout,
                                             user=user)

                # check if we are on a branch to merge changes
                cmd = "git symbolic-ref -q HEAD > /dev/null"
                retcode = __salt__['cmd.retcode'](cmd, python_shell=True, cwd=target, user=user)
                # XXX: the real different with git.latest is here
                # we pull
                # but also fetch and merge --only-ff in case of errors
                if 0 == retcode:
                    method = 'git.fetch' if bare else 'git.pull'
                    def pull():
                        __salt__[method](
                            target,
                            opts=fetch_opts,
                            user=user,
                            identity=identity)
                    try:
                        pull()
                    except (Exception,) as ex:
                        ex_msg = ex.message.lower()
                        # if the pb is the remote branch not being set
                        # just set it and run pull again
                        if(
                            ("--set-upstream" in ex_msg)
                            and firstrun
                            and len(branch) > 0
                            and branch == rev
                        ):
                            cmd = 'git branch --set-upstream {branch} origin/{rev}'.format(
                                branch=branch,
                                rev=rev,
                            )
                            __salt__['cmd.run_stdout'](cmd,
                                                       cwd=target,
                                                       python_shell=True,
                                                       user=user)
                            pull()
                        else:
                            if (
                                (method == 'git.fetch')
                                or
                                (not 'local changes' in ex_msg)
                            ):
                                raise
                            __salt__['git.fetch'](
                                target,
                                opts=fetch_opts,
                                user=user,
                                identity=identity)
                            __salt__['git.fetch'](
                                target,
                                opts='--tags',
                                user=user,
                                identity=identity)
                            __salt__['git.merge'](
                                target,
                                opts='--ff-only',
                                user=user)
                if submodules:
                    __salt__['git.submodule'](target,
                                              user=user,
                                              identity=identity,
                                              opts='--recursive')

                new_rev = __salt__['git.revision'](cwd=target, user=user)
        except Exception as exc:
            return _fail( ret, str(exc))

        if current_rev != new_rev:
            log.info('Repository {0} updated: {1} => {2}'.format(target,
                                                                 current_rev,
                                                                 new_rev))
            ret['comment'] = 'Repository {0} updated'.format(target)
            ret['changes']['revision'] = '{0} => {1}'.format(
                current_rev, new_rev)
    else:
        # KISS: let do the rest of the job by original git.latest
        locs = globals()
        locs.update(locals())
        for i in [
            '__env__',
            '__grains__',
            '__lowstate__',
            '__opts__',
            '__package__',
            '__pillar__',
            '__running__',
            '__salt__',
        ]:
            if not hasattr(git, i):
                setattr(git, i, locs[i])
        return git.latest(
            name,
            rev=rev,
            target=target,
            user=user,
            force=force,
            force_checkout=force_checkout,
            submodules=submodules,
            mirror=mirror,
            bare=bare,
            remote_name=remote_name,
            always_fetch=always_fetch,
            identity=identity,
            onlyif=onlyif,
            unless=unless)
    return ret


def latest(*args, **kwargs):
    '''
    Compat wrapper
    '''
    # KISS: let do the rest of the job by original git.latest
    locs = globals()
    locs.update(locals())
    for i in [
        '__env__',
        '__grains__',
        '__lowstate__',
        '__opts__',
        '__package__',
        '__pillar__',
        '__running__',
        '__salt__',
    ]:
        if not hasattr(git, i):
            setattr(git, i, locs[i])
    return git.latest(*args, **kwargs)
