from app.models.streams import ActivityStream

__author__ = 'arshad'


from bson import ObjectId, json_util
from app.models import Node, ACTIVITY, ADVENTURE, TRIP, EVENT, PROFILE, ARTICLE, BLOG, POST, DISCUSSION, STREAM
from app.models.activity import Activity
from app.models.adventure import Adventure
from app.models.content import Article, Post, Discussion, Blog
from app.models.event import Event
from app.models.profile import Profile
from flask import render_template, g
from mongoengine import Document
import simplejson
from bson.json_util import dumps
from bson import Binary, Code
from app.models.trip import Trip


__author__ = 'arshad'

import json

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class NodeExtractor(object):

    def __init__(self, filters):
        self.filters = filters

    def get_list(self, paged, page, size):
        print '[*]', paged, page, size
        if paged:
            page = int(page)
            start = (page - 1) * size
            end = start + size
            return self.get_query().all()[start: end]
        else:
            return self.get_query().all()

    def get_single(self):
        return self.get_query().first()

    def get_query(self):
        if len(self.filters) > 0:
            filters = {}
            for k, v in self.filters.iteritems():
                if '__' in k:
                    fields = k.split('__')
                    assert len(fields) is 3
                    __filters = {}
                    __filters[fields[2]] = v
                    __node = NodeExtractor.factory(fields[1], __filters).get_single()
                    filters[fields[0]] =  __node
                else:
                    filters[k] = v
            return self.model_class().objects(**filters)
        return self.model_class().objects

    def model_class(self):
        raise Exception("Not implemented")


    @classmethod
    def factory(cls, model_name, filters=None):
        if type(model_name) == type:
            model_name = model_name.__name__
        model_name = model_name.lower().strip()
        if model_name == ACTIVITY:
            cls = ActivityExtractor
        elif model_name == ADVENTURE:
            cls = AdventureExtractor
        elif model_name == TRIP:
            cls = TripExtractor
        elif model_name == EVENT:
            cls = EventExtractor
        elif model_name == PROFILE:
            cls = ProfileExtractor
        elif model_name == ARTICLE:
            cls =ArticleExtractor
        elif model_name == BLOG:
            cls = BlogExtractor
        elif model_name == POST:
            cls = PostExtractor
        elif model_name == DISCUSSION:
            cls = DiscussionExtractor
        elif model_name == STREAM:
            cls = ActivityStreamExtractor
        else:
            raise Exception("Invalid model name for extractor")
        return cls(filters)

class ActivityStreamExtractor(NodeExtractor):

    def model_class(self):
        return ActivityStream

class ArticleExtractor(NodeExtractor):

    def model_class(self):
        return Article


class BlogExtractor(NodeExtractor):

    def model_class(self):
        return Blog


class DiscussionExtractor(NodeExtractor):

    def model_class(self):
        return Discussion



class PostExtractor(NodeExtractor):

    def model_class(self):
        return Post


class ActivityExtractor(NodeExtractor):

    def model_class(self):
        return Activity

class AdventureExtractor(NodeExtractor):

    def model_class(self):
        return Adventure



class EventExtractor(NodeExtractor):

    def model_class(self):
        return Event


class TripExtractor(NodeExtractor):

    def model_class(self):
        return Trip


class ProfileExtractor(NodeExtractor):

    def model_class(self):
        return Profile

