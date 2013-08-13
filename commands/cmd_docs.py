# -*- coding: utf-8 -*-

import sys
import bson
import pymongo

from kobo.client import ClientCommand


def get_ip_from_leases(mac):
    cmd = ('cat /var/lib/libvirt/dnsmasq/default.leases |'
           'grep "%s"' % mac)
    rc, out = run(cmd, can_fail=True)
    if int(rc):
        return None
    return out.split(' ')[2]


def get_mac(name):
    cmd = ('sudo virsh dumpxml "%s"' % name)
    rc, out = run(cmd, can_fail=True)
    if int(rc):
        return None
    content = fromstring(out)

    output = []
    ifsel = CSSSelector('interface[type="network"]')
    macsel = CSSSelector('mac')
    for interface in ifsel(content):
        hwaddr = macsel(interface)[0]
        output.append(hwaddr.get('address'))
    return output


class Docs(ClientCommand):
    """documentation database"""
    enabled = True

    def options(self):
        self.parser.usage = ('%%prog %s <command> <text>'
                             % self.normalized_name)
        self.parser.add_option('-t',  '--title',
                               action='store',
                               dest='title',
                               default=None,
                               help=('documentation title (required '
                                     'when adding new documentation '
                                     'step)'))
        self.parser.add_option('-s', '--step',
                               action='store',
                               dest='step',
                               type='int',
                               default=None,
                               help='step in documentation')
        self.parser.add_option('-i', '--id',
                               action='store',
                               dest='docid',
                               default=None,
                               help='documentation id')

    def run(self, *args, **kwargs):
        try:
            command, text = args[0], args[1:]
            text = ' '.join(text)
        except ValueError:
            self.parser.error('Please specify command '
                              '(add|remove|search).')

        docid = kwargs.get('docid')
        title = kwargs.get('title')
        step = kwargs.get('step')

        mongod_url = self.conf.get('MONGODB_URL')
        mongod_port = self.conf.get('MONGODB_PORT')

        client = pymongo.MongoClient(mongod_url, mongod_port)
        coll = client.borga.documentation

        if command == 'add':
            # add new documentation
            if not title and not docid:
                self.parser.error('Adding new steps requires option '
                                  'title')
            if not text:
                self.parser.error('Please specify also documentation '
                                  'text to add')

            if docid:
                query = {'_id': bson.objectid.ObjectId(docid)}
            else:
                dbtitle = title.strip().lower()
                query = {'title': dbtitle}
            record = coll.find_one(query)

            docsteps = record and record['steps'] or []
            if step is not None:
                docsteps.insert(step, text)
            else:
                docsteps.append(text)
            coll.update(query, {'$set': {'steps': docsteps}},
                        upsert=True)

        elif command == 'search':
            # search documentation
            if not text:
                self.parser.error('Please specify also documentation '
                                  'text to search in titles.')
            if docid:
                query = {'_id': bson.objectid.ObjectId(docid)}
            else:
                # TO-DO: Change this to fulltext search instead
                query = {'title': {'$regex': '.*%s.*' % text,
                                   '$options': 'i'}}

            record = coll.find(query)
            if record.count() == 0:
                sys.stdout.write('Not found.\n')
                sys.stdout.flush()
                sys.exit(0)

            for docfile in record:
                sys.stdout.write('%(title)s [%(_id)s]\n' % docfile)
                for docstep in docfile['steps']:
                    sys.stdout.write('    - %s\n' % docstep)
            sys.stdout.flush()

        elif command == 'remove':
            # remove documentation
            if not title and not docid:
                self.parser.error('Removing documentation requires ID '
                                  'or title')
            if step is None:
                # remove documentation document
                if docid:
                    query = {'_id': bson.objectid.ObjectId(docid)}
                else:
                    dbtitle = title.strip().lower()
                    query = {'title': dbtitle}
                coll.remove(query)
            else:
                # remove documentation step
                if docid:
                    query = {'_id': bson.objectid.ObjectId(docid)}
                else:
                    dbtitle = title.strip().lower()
                    query = {'title': dbtitle}

                record = coll.find_one(query)
                if not record:
                    self.parser.error('Record with given query does '
                                      'not exists.')
                record['steps'].pop(step)
                coll.update(query, {'$set': {'steps': record['steps']}})

        else:
            self.parser.error('Unknown documentation command %s'
                              % command)
