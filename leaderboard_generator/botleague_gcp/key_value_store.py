from __future__ import print_function

import leaderboard_generator.botleague_gcp.constants as c


def get_key_value_store():
    if c.SHOULD_USE_FIRESTORE:
        return SimpleKeyValueStoreFirestore()
    else:
        return SimpleKeyValueStoreLocal()


class SimpleKeyValueStoreFirestore(object):
    def __init__(self):
        self.collection_name = 'simple_key_value_store'
        from firebase_admin import firestore
        self.kv = firestore.client().collection(self.collection_name)

    def get(self, key):
        value = self.kv.document(self.collection_name).get().to_dict()[key]
        return value

    def set(self, key, value):
        self.kv.document(key).set({key: value})


class SimpleKeyValueStoreLocal(object):
    def __init__(self):
        self.kv = {}

    def get(self, key):
        return self.kv[key]

    def set(self, key, value):
        self.kv[key] = value
