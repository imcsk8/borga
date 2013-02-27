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
            self._bugzilla = bugzilla.RHBugzilla(url=url, user=user,
                                                 password=password,
                                                 cookiefile=cookiefile)
        except xmlrpclib.Error, ex:
            raise self.Error('Connection to Bugzilla failed: %s' % ex)

    def __getattr__(self, attr):
        return getattr(self._bugzilla, attr)

    def _get_bug(self, bug_id):
        try:
            bug = self._bugzilla.getbug(bug_id)
        except xmlrpclib.Fault:
            raise self.Error('Bug #%s does not exist.' % bug_id)

    def _update_bug(self, bug, **kwargs):
        """
        Most helpful:
            assigned_to, comment, keywords_add, keywords_remove,
            priority, severity, target_milestone, status, fixed_in
        More at:
            http://git.fedorahosted.org/cgit/python-bugzilla.git/tree/bugzilla/bugzilla4.py#n57
        """
        try:
            update = self._bugzilla.build_update(**kwargs)
            return self._bugzilla.update_bugs(bug.bug_id, update)
        except xmlrpclib.Fault, ex:
            raise self.Error('Failed to add comment to the given '
                             'bug #%s:\n%s' % (bug_id, ex))

    def add_comment(self, bug_id, comment):
        """
        Adds comment to the given bug. Raises BZConnector.Error in case
        of failure.
        """
        bug = self._get_bug(bug_id)
        self._update_bug(bug, comment=comment)

    def get_bugs(self, **kwargs):
        """
        Returns result of BZ query according to given kwargs.
        """
        try:
            return self._bugzilla.query(kwargs)
        except xmlrpclib.Fault, ex:
            raise self.Error('Bugzilla query failed:\n%s' % ex)

    def check_bugs(self, product, component, flags, owner=None,
                   status='POST'):
        """
        Checks if all bugs of given product/component in status POST
        owned by owner have necessary flags.
        """
        failed = {}
        flags = flags or []
        kwargs = {'product': product, 'component': component,
                  'assigned_to': owner, 'status': status}
        for bug in self.get_bugs(**kwargs):
            flg_map = dict([(i['name'], i) for i in bug.flags])
            for flg in flags:
                if flg not in flg_map or \
                   flg_map[flg].get('status', '-') != '+':
                    failed.setdefault(flg, []).append(bug.bug_id)
        return failed

    def finalize_bugs(self, product, component, owner=None,
                      fixed_in=None, comment=None, pre_status='POST',
                      post_status='MODIFIED'):
        """
        Sets all bugs of given product/component in status POST owned
        by owner to MODIFIED. Returns list of modified bugs.
        """
        modified = []
        kwargs = {'product': product, 'component': component,
                  'assigned_to': owner, 'status': pre_status}
        for bug in self.get_bugs(**kwargs):
            self._update_bug(bug, fixed_in=fixed_in, status=post_status,
                             comment=comment)
            modified.append(bug.bug_id)
        return modified
