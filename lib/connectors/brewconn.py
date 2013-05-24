# -*- coding: utf-8 -*-


class BrewConnector(object):
    """
    Object used for communitation with Brew or Koji
    """
    class Error(Exception):
        pass

    def __init__(self, url, hubtype='brew'):
        if hubtype == 'brew':
            import brew
            self._service = brew.ClientSession(url)
            self._err = brew.BrewError
        elif hubtype == 'koji':
            import koji
            self._service = koji.ClientSession(url)
            self._err = koji.KojiError
        else:
            raise self.Error('Unknown hub type')

    def __getattr__(self, attr):
        return getattr(self._service, attr)

    def get_newest_build(self, package, tags, arch='src'):
        """
        Returns the newest build of the given package built under
        the given tags.
        """
        svc = self._service
        for tag in tags:
            try:
                return svc.getLatestBuilds(tag, package=package)[0]
            except (IndexError, self._err):
                continue
