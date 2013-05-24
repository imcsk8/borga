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

    def _get_bug(self, bug_id):
        try:
            bug = self._bugzilla.getbug(bug_id)
        except xmlrpclib.Fault:
            raise self.Error('Bug #%s does not exist.' % bug_id)

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
                #flag = {'name': parts[0], 'status': state}
                #if state == '?':
                #    flag['requestee'] = self._user
                flags.append({'name': parts[0], 'status': state})
            if not hasstate:
                flags.append({'name': flg, 'status': ''})
        if flags:
            try:
                self._bugzilla.update_flags([bug.bug_id], flags)
            except xmlrpclib.Fault, ex:
                raise self.Error('Failed to update given bug #%s:\n%s'
                                 % (bug_id, ex))

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
        self.update_bug(bug, comment=comment)

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

    def filter_by_flags(self, buglist, flags, state, negative=False):
        output = {}
        for bug in buglist:
            flg_map = dict([(i['name'], i) for i in bug.flags])
            for flg in flags:
                if flg not in flg_map:
                    if negative:
                        output.setdefault(flg, []).append(bug.bug_id)
                    continue

                flg_status = flg_map[flg].get('status', '-')
                if (negative and flg_status != state) or \
                   (not negative and flg_status == state):
                    output.setdefault(flg, []).append(bug.bug_id)
        return output

    def check_bugs(self, product, component, flags, owner=None,
                   status='POST'):
        """
        Checks if all bugs of given product/component in status POST
        owned by owner have necessary flags.
        """

        flags = flags or []
        kwargs = {'product': product, 'component': component,
                  'status': status, 'assigned_to': owner}
        bugs = self.get_bugs(**kwargs)
        return self.filter_by_flags(bugs, flags, '+', negative=True)
