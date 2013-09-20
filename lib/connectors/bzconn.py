# -*- coding: utf-8 -*-

import bugzilla
import xmlrpclib


class BZConnector(object):
    """
    Object used for communitation with Bugzilla via XML-RPC
    """
    class Error(Exception):
        pass

    def __init__(self, url, user=None, password=None, cookiefile=None):
        try:
            self._user = user
            self._bugzilla = bugzilla.RHBugzilla(url=url, user=user,
                                                 password=password,
                                                 cookiefile=cookiefile)
        except xmlrpclib.Error, ex:
            raise self.Error('Connection to Bugzilla failed: %s' % ex)

    def __getattr__(self, attr):
        return getattr(self._bugzilla, attr)

    def get_bug(self, bug_id):
        """
        Returns single bug.
        """
        try:
            return self._bugzilla.getbug(bug_id)
        except xmlrpclib.Fault:
            raise self.Error('Bug #%s does not exist.' % bug_id)

    def get_bugs(self, **kwargs):
        """
        Returns result of BZ query according to given kwargs.
        """
        clean = {}
        for key, value in kwargs.iteritems():
            if value is not None:
                clean[key] = value
        try:
            return self._bugzilla.query(clean)
        except xmlrpclib.Fault, ex:
            raise self.Error('Bugzilla query failed:\n%s' % ex)

    def update_bug(self, bug, **kwargs):
        """
        Most helpful:
            assigned_to, comment, keywords_add, keywords_remove,
            priority, severity, target_milestone, status, fixed_in
        More at:
            http://git.fedorahosted.org/cgit/python-bugzilla.git/tree/bugzilla/bugzilla4.py#n57
        Flags:
            just use flags=['flag+', 'yaf?']
        """
        flags = []
        for flg in kwargs.pop('flags', []):
            hasstate = False
            for state in ('+', '?', '-'):
                parts = flg.split(state)
                if len(parts) < 2:
                    continue
                hasstate = True
                flags.append({'name': parts[0], 'status': state})
            if not hasstate:
                flags.append({'name': flg, 'status': ''})
        try:
            if flags:
                self._bugzilla.update_flags([bug.bug_id], flags)
            update = self._bugzilla.build_update(**kwargs)
            return self._bugzilla.update_bugs(bug.bug_id, update)
        except xmlrpclib.Fault, ex:
            raise self.Error('Failed to update bug #%s:\n%s' % (bug_id, ex))

    def add_comment(self, bug_id, comment):
        """
        Adds comment to the given bug. Raises BZConnector.Error in case
        of failure.
        """
        bug = self._get_bug(bug_id)
        self.update_bug(bug, comment=comment)

    def filter_by_flags(self, bugs, flags, negative=False):
        output = []
        fno = len(flags)
        for bug in bugs:
            bno = 0
            for flag in bug.flags:
                if ((not negative and '%(name)s%(status)s' % flag in flags)
                    or negative):
                    bno += 1
            # add bug to result only if it has all required flags
            if fno == bno:
                output.append(bug)
        return output

    def filter_by_ids(self, bugs, ids):
        output = []
        for bug in bugs:
            if str(bug.bug_id).strip('#') not in ids:
                continue
            output.append(bug)
        return output

    def filter_by_target(self, bugs, target):
        # this is quite time consuming, but the only way how to correctly filter
        # by target release
        output = []
        for bug in bugs:
            _bug = self.get_bug(bug.bug_id)
            if _bug.target_release[0] != target:
                continue
            output.append(_bug)
        return output
