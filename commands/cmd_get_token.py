# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import pymongo
import struct
import sys

from kobo.client import ClientCommand


class Get_Token(ClientCommand):
    """
    LinOTP counter-based soft-token for poor people who do not have
    Android or iOS available
    """
    enabled = True

    def options(self):
        self.parser.usage = '%%prog %s' % self.normalized_name

    def run(self, *args, **kwargs):
        secret = self.conf.get('SECRET')
        mongod_url = self.conf.get('MONGODB_URL')
        mongod_port = self.conf.get('MONGODB_PORT')

        client = pymongo.MongoClient(mongod_url, mongod_port)
        coll = client.borga.variables
        coll.update({'name': 'token_counter'}, {'$inc': {'value': 1}},
                    upsert=True)
        counter = coll.find_one({'name': 'token_counter'})

        try:
            key = base64.b32decode(secret, True)
        except TypeError:
            secret += "=" * ((8 - len(secret) % 8) % 8)
            key = base64.b32decode(secret, True)
        msg = struct.pack(">Q", counter['value'])
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = ord(h[19]) & 15
        token = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
        token = str(token)
        if len(token) < 6:
            token = '0' * (6 - len(token)) + token
        sys.stdout.write('Valid token: %s\n' % token)
