from bson import ObjectId
from mongoengine import Q
from app.models import ACTIVITY, ADVENTURE, TRIP, EVENT, PROFILE, ARTICLE, POST, DISCUSSION, STREAM, RELATIONSHIPS, LOCATION, \
    PROFILE_TYPE, ADVERTISEMENT, CHANNEL, NodeFactory
from app.models.streams import ActivityStream
from app.models.activity import Activity
from app.models.adventure import Adventure, Location
from app.models.content import Article, Post, Discussion, Advertisement, Channel
from app.models.event import Event
from app.models.profile import Profile, ProfileType
from app.models.relationships import RelationShips
from app.models.trip import Trip
from app.utils import convert_query_to_filter

__author__ = 'arshad'

import json, datetime

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class NodeExtractor(object):


    def __init__(self, model_name, init_filters={}):
        self.model_class = NodeFactory.get_class_by_name(model_name)
        self.init_filters = init_filters

    def get_list(self, query, paged, page, size):
        query_set = self.get_query(query)
        if paged:
            page = int(page)
            size = int(size)
            start = (page - 1) * size
            end = start + size
            models = query_set.all()[start: end]
        else:
            models = query_set.all()
        if models and len(models) > 0:
            models = [u for u in list(models)]
            for u in models:
                if hasattr(u, 'on_get') and callable(u.on_get):
                    u.on_get()
        return models

    def get_single(self, query):
        return self.get_query(query).first()

    def last_page(self, query, size):
        query_set = self.get_query(query)
        count = query_set.count()
        page = (count / int(size)) + 1
        return page

    def get_query(self, query):
        use_filters = convert_query_to_filter(query)
        filters = self.init_filters
        merge = []
        if len(use_filters) > 0:
            filters = {}
            for k, v in use_filters.iteritems():
                if not isinstance(v, str) and not isinstance(v, unicode):
                    filters[k] = v
                    continue
                elif '|' in v:
                    u = v.split('|')
                    if u[0] == 'bool':
                        v = True if u[1].strip() in ('True', '1', 1) else False
                    elif u[0] == 'int':
                        v = int(u[1])
                    elif u[0] == 'float':
                        v = float(u[1])
                    else:
                        v = str(u[1])

                if k.startswith('relationship'):
                    fields = k.split('__')
                    assert len(fields) >= 3
                    relationship = fields[1]
                    from_node_type = fields[2]
                    from_node = NodeExtractor.factory(from_node_type).get_single('pk:%s' % v)
                    nodes = RelationShips.get_by_query(from_node, relationship)
                    filters['id__in'] = [u.id for u in nodes if u is not None and hasattr(u, 'id')]
                elif '__' in k:
                    fields = k.split('__')
                    if len(fields) >= 3:
                        __node = NodeExtractor.factory(fields[1]).get_single('%s:%s' % (fields[2], str(v)))
                        if len(fields) == 4:
                            f = "%s__%s" % (fields[0], fields[3])
                        else:
                            f = fields[0]
                        filters[f] =  __node
                    elif len(fields) == 2 and fields[1] == 'in':
                        _values = [u.strip() for u in v.split(',') if u and u.strip() and len(u.strip()) > 0]
                        filters[k] = _values
                        merge.append(fields[0])
                    else:
                        if 'date' in k:
                            yy, mm, dd = v.split('-')
                            filters[k] = datetime.datetime(int(yy), int(mm), int(dd))
                        else:
                            filters[k] = v
                else:
                    filters[k] = v

            if len(merge) > 0:
                to_add = []
                for m in merge:
                    if not filters.has_key(m):
                        continue
                    for k in filters.keys():
                        if k.startswith(m) and k.endswith('in'):
                            to_add.append((m, k, filters[m]))
                if len(to_add) > 0:
                    for m, k, v in to_add:
                        del filters[m]
                        filters[k].append(v)
        print filters
        return self.model_class.objects(**filters).order_by('-created_timestamp')

    @classmethod
    def factory(cls, model_name):
        if type(model_name) == type:
            model_name = model_name.__name__
        model_name = model_name.lower().strip()
        if model_name == ACTIVITY:
            return activity_extractor
        elif model_name == ADVENTURE:
            return adventure_extractor
        elif model_name == TRIP:
            return trip_extractor
        elif model_name == EVENT:
            return event_extractor
        elif model_name == PROFILE:
            return profile_extractor
        elif model_name == ARTICLE:
            return article_extractor
        elif model_name == POST:
            return post_extractor
        elif model_name == DISCUSSION:
            return discussion_extractor
        elif model_name == STREAM:
            return stream_extractor
        elif model_name == RELATIONSHIPS:
            return relationship_extractor
        elif model_name == LOCATION:
            return location_extractor
        elif model_name == PROFILE_TYPE:
            return profile_type_extractor
        elif model_name == ADVERTISEMENT:
            return advertisement_extractor
        elif model_name == CHANNEL:
            return channel_extractor
        else:
            raise Exception("Invalid model name for extractor")

stream_extractor = NodeExtractor(STREAM)
activity_extractor = NodeExtractor(ACTIVITY)
advertisement_extractor = NodeExtractor(ADVERTISEMENT)
channel_extractor = NodeExtractor(CHANNEL)
profile_type_extractor = NodeExtractor(PROFILE_TYPE)
location_extractor = NodeExtractor(LOCATION)
article_extractor = NodeExtractor(ARTICLE)
discussion_extractor = NodeExtractor(DISCUSSION)
post_extractor = NodeExtractor(POST)
adventure_extractor = NodeExtractor(ADVENTURE)
event_extractor = NodeExtractor(EVENT)
trip_extractor = NodeExtractor(TRIP)
profile_extractor = NodeExtractor(PROFILE, init_filters=dict(type__ne=ProfileType.objects(name__iexact='Subscription Only').first()))
all_profile_extractor = NodeExtractor(PROFILE)
relationship_extractor = NodeExtractor(RELATIONSHIPS)
