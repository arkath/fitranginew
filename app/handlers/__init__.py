from app.utils import convert_query_to_filter

__author__ = 'arshad'

from flask import g
from app.handlers.extractors import NodeExtractor, article_extractor, advertisement_extractor, adventure_extractor, \
    activity_extractor, discussion_extractor, profile_type_extractor, event_extractor, profile_extractor, \
    trip_extractor, post_extractor, stream_extractor
from app.models import ACTIVITY, ADVENTURE, EVENT, TRIP, PROFILE, DISCUSSION, ARTICLE, POST, STREAM, Node, ADVERTISEMENT
from app.models.streams import ActivityStream
from app.models.content import Content, Post, Article, Discussion
from app.models.adventure import Adventure, Location
from app.models.activity import Activity
from app.models.event import Event
from app.models.trip import Trip
from app.models.profile import Profile, ProfileType

ICON_VIEW, GRID_VIEW, ROW_VIEW, GRID_ROW_VIEW, DETAIL_VIEW = 'icon', "grid", "row", "grid-row", "detail"

COLLECTION_PATHS = {
    STREAM: 'site/pages/searches/streams',
    ADVENTURE: 'site/pages/searches/adventures',
    PROFILE: 'site/pages/searches/profiles',
    POST: 'site/pages/searches/posts',
    DISCUSSION: 'site/pages/searches/discussions',
    EVENT: 'site/pages/searches/events',
    ARTICLE: 'site/pages/searches/articles',
    TRIP: 'site/pages/searches/trips',
    "explore": 'site/pages/landings/home',
    "community": 'site/pages/landings/community',
}

class View(object):

    def get_card(self):
        raise Exception('Not Implemented')

    def get_title(self):
        raise Exception('Not Implemented')


class EditorView(View):

    def __init__(self, model_name, id=None):
        self.model_name = model_name
        self.id = id

    def get_title(self):
        return 'Fitrangi: Edit' + self.model_name

    def get_card(self):
        if self.id:
            extractor = NodeExtractor.factory(self.model_name)
            model = extractor.get_single("pk:%s;" % str(self.id) )
            if not g.user:
                print 'User not logged in'
                raise Exception("where is the user")
            if model and model.author.id != g.user.id or 'Admin' not in g.user.roles:
                print 'not the same user'
                raise Exception("Invalid User")
        else:
            model = None

        from app.views import env
        template_path = 'site/includes/content-editor.html'
        template = env.get_template(template_path)
        from app.views import force_setup_context
        context = force_setup_context({})
        context['model'] = model
        context['model_name'] = self.model_name
        context['is_edit'] = True if model else False
        return template.render(**context)

class CollectionView(object):

    def __init__(self, model_name, category):
        self.model_name = model_name
        self.category = category

    @classmethod
    def build(cls, model_name, card_type, category='all'):
        if card_type == 'row':
            return RowCollectionView(model_name, category)
        elif card_type == 'grid':
            return GridCollectionView(model_name, category)
        elif card_type == 'icon':
            return IconCollectionView(model_name, category)
        else:
            return GridRowCollectionView(model_name, category)

    def get_card(self, context={}):
        from app.views import env
        template_path = 'site/pages/collections/' + self.card_type + '.html'
        template = env.get_template(template_path)
        context['category'] = self.category
        context['model_name'] = self.model_name
        context['card_type'] = self.card_type
        html = template.render(**context)
        return html

    def only_list(self, models):
        return self.__get_model_cards(models)

    def __get_model_cards(self, models):
        if len(models) > 0:

            def iterate_models(models):
                for model in models:
                    print model
                    temp = NodeView.get_collection_card(self.model_name, self.card_type, model)
                    yield model, temp

            return ''.join(u[1] for u in iterate_models(models))
        else:
            return ''

    def _get_template_path(self):
        raise Exception('Not implemented')


class IconCollectionView(CollectionView):
    def __init__(self, model_name, category='all'):
        super(IconCollectionView, self).__init__(model_name, category)
        self.card_type = 'icon'

class RowCollectionView(CollectionView):
    def __init__(self, model_name, category='all'):
        super(RowCollectionView, self).__init__(model_name, category)
        self.card_type = 'row'

class GridCollectionView(CollectionView):
    def __init__(self, model_name, category='all'):
        super(GridCollectionView, self).__init__(model_name, category)
        self.card_type = 'grid'

class GridRowCollectionView(CollectionView):
    def __init__(self, model_name, category='all'):
        super(GridRowCollectionView, self).__init__(model_name, category)
        self.card_type = 'grid-row'

class CollectionType(object):

    def __init__(self, collection_view):
        self.collection_view = collection_view

    def only_list(self, models):
        return self.collection_view.only_list(models)

    def get_card(self, context={}):
        from app.views import env
        card = self.collection_view.get_card(context)
        context.update(dict(list_container=card))
        template_path = self._get_template()
        template = env.get_template(template_path)
        html = template.render(**context)
        return html


class FixedCollection(CollectionType):

    def __init__(self, collection_view):
        super(FixedCollection, self).__init__(collection_view)

    def _get_template(self):
        return 'site/pages/collections/fixed.html'

class ScrollableCollection(CollectionType):

    def __init__(self, collection_view, is_last_page=False):
        super(ScrollableCollection, self).__init__(collection_view)
        self.is_last_page = is_last_page

    def _get_template(self):
        return 'site/pages/collections/scrollable.html'


class NodeCollectionFactory(object):

    @classmethod
    def resolve(cls, model_name, card_type, category='all', is_scrollable=True):
        collection_view = CollectionView.build(model_name, card_type, category)
        if is_scrollable:
            return ScrollableCollection(collection_view)
        else:
            return FixedCollection(collection_view)


class NodeView(View):

    @classmethod
    def get_collection_card(cls, model_name, card_type, model, context={}):
        from app.views import env
        from app.views import force_setup_context
        template_path = 'site/models/' + model_name + '/' + card_type + ".html"
        context = force_setup_context(context)
        context['model'] = model
        print '[*] Test Card:', model_name, model, template_path
        if model_name == STREAM:
            if model.is_post_activity:
                template_path = 'site/models/post/row.html'
                context['model'] = model.object
            else:
                if model.is_entity_activity:
                    if model.object and model.object.id:
                        m_name, id = (model.object.__class__.__name__.lower(), str(model.object.id))
                        if m_name == 'profile':
                            c_type = ICON_VIEW
                        else:
                            c_type = GRID_VIEW
                        entity_view =  NodeView.get_collection_card(m_name, c_type, NodeExtractor.factory(m_name).get_single("pk:%s" % id), {})
                        context['entity_view'] = entity_view
        template = env.get_template(template_path)
        return template.render(**context)


    @classmethod
    def get_detail_card(cls, model_name, model, context={}):
        from app.views import env
        from app.views import force_setup_context
        template_path = 'site/models/' + model_name + '/detail.html'
        template = env.get_template(template_path)
        context = force_setup_context(context)
        context['model'] = model
        return template.render(**context)

class PageManager(object):

    @classmethod
    def get_detail_title_and_page(cls, model_name, **kwargs):
        query = kwargs.get('query', None)
        user = kwargs.get('user', None)
        assert  query is not None
        model = NodeExtractor.factory(model_name).get_single(query)
        context = dict(parent=model, user=user, query=query, filters=convert_query_to_filter(query))
        context.update(Page.factory(model_name, 'detail').get_context(context))
        title = model.name if hasattr(model, 'name') and model.name is not None else (model.title if hasattr(model, 'title') and model.title is not None else 'Fitrangi: India\'s complete adventure portal')
        return title, NodeView.get_detail_card(model_name, model, context), context

    @classmethod
    def get_search_title_and_page(cls, model_name, **kwargs):
        query = kwargs.get('query', None)
        user = kwargs.get('user', None)
        from app.views import env
        from app.views import force_setup_context
        template_path = COLLECTION_PATHS.get(model_name) + '.html'
        print 'Loading template: ', template_path
        template = env.get_template(template_path)
        context = dict(user=user, query=query, filters=convert_query_to_filter(query))
        context = force_setup_context(context)
        context.update(Page.factory(model_name, 'search').get_context(context))
        html = template.render(**context)
        print len(html)
        return 'Fitrangi: India\'s complete adventure portal. Find what you are looking for', html, context

    @classmethod
    def get_landing_title_and_page(cls, model_name, **kwargs):
        from app.views import env
        from app.views import force_setup_context
        query = kwargs.get('query', None)
        user = kwargs.get('user', None)
        template_path = COLLECTION_PATHS.get(model_name) + '.html'
        template = env.get_template(template_path)
        context = dict(user=user, query=query, filters=convert_query_to_filter(query))
        context = force_setup_context(context)
        context.update(Page.factory(model_name, 'landing').get_context(context))
        html = template.render(**context)
        return 'Fitrangi: India\'s complete adventure portal. Find what you are looking for', html, context


class Page(object):

    def __init__(self, model_name):
        self.model_name = model_name

    def get_context(self, context):
        raise Exception('Unimplemented')

    @classmethod
    def factory(self, model_name, type):
        if type == 'detail':
            if model_name == ACTIVITY:
                return article_detail_page
            elif model_name == ADVENTURE:
                return adventure_detail_page
            elif model_name == PROFILE:
                return profile_detail_page
            elif model_name == ARTICLE:
                return article_detail_page
            elif model_name == DISCUSSION:
                return discussion_detail_page
            else:
                raise Exception("Not implemented")
        elif type == 'search':
            if model_name == ADVENTURE:
                return adventure_search_page
            elif model_name == PROFILE:
                return profile_search_page
            elif model_name == ARTICLE:
                return article_search_page
            elif model_name == DISCUSSION:
                return discussion_search_page
            elif model_name == EVENT:
                return event_search_page
            else:
                raise Exception("Not implemented")
        elif type == 'landing':
            if model_name == 'explore':
                return explore_landing_page
            elif model_name == 'community':
                return community_landing_page
            else:
                raise Exception("Not implemented")
        else:
            raise Exception("Invalid argument")

class LandingPage(Page):

    def __init__(self, model_name):
        super(LandingPage, self).__init__(model_name)

    def get_context(self, context):
        if self.model_name == 'explore':
            counters = dict(adventure=Adventure.objects.count(),
                            profile=Profile.objects(type__ne=ProfileType.objects(name__iexact='subscription only').first()).count(),
                            discussion=Discussion.objects.count(),
                            article=Article.objects.count())
            journal = NodeCollectionFactory.resolve(ARTICLE, GRID_VIEW, is_scrollable=False).get_card(context)
            enthusiast_profile = NodeCollectionFactory.resolve(PROFILE, GRID_VIEW, is_scrollable=False, category='enthusiast').get_card(context)
            organizer_profile = NodeCollectionFactory.resolve(PROFILE, GRID_VIEW, is_scrollable=False, category='organizer').get_card(context)
            event = NodeCollectionFactory.resolve(EVENT, GRID_VIEW, is_scrollable=False).get_card(context)
            discussion = NodeCollectionFactory.resolve(DISCUSSION, ROW_VIEW, is_scrollable=False).get_card(context)
            return dict(counters=counters, journal=journal, enthusiast_profile=enthusiast_profile, organizer_profile=organizer_profile, event=event, discussion=discussion)
        elif self.model_name == 'community':
            profile = NodeCollectionFactory.resolve(PROFILE, ICON_VIEW, is_scrollable=False).get_card(context)
            event = NodeCollectionFactory.resolve(EVENT, GRID_VIEW, is_scrollable=False).get_card(context)
            discussion = NodeCollectionFactory.resolve(DISCUSSION, ROW_VIEW, is_scrollable=False).get_card(context)
            return dict(profile=profile, event=event, discussion=discussion)
        else:
            raise Exception('Not implemented')

class SearchPage(Page):

    def __init__(self, model_name):
        super(SearchPage, self).__init__(model_name)

    def get_context(self, context):
        if self.model_name == ADVENTURE:
            return dict(adventure_list=NodeCollectionFactory.resolve(ADVENTURE, GRID_VIEW).get_card(context))
        elif self.model_name == PROFILE:
            return dict(profiles_list=NodeCollectionFactory.resolve(PROFILE, ROW_VIEW).get_card(context))
        elif self.model_name == ARTICLE:
            all = NodeCollectionFactory.resolve(ARTICLE, GRID_VIEW).get_card(context)
            top = NodeCollectionFactory.resolve(ARTICLE, ROW_VIEW, category='top').get_card(context)
            my = NodeCollectionFactory.resolve(ARTICLE, ROW_VIEW, category='my').get_card(context)
            advertisement_list = NodeCollectionFactory.resolve(ADVERTISEMENT, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            return dict(all=all, top=top, my=my, advertisement_list=advertisement_list)
        elif self.model_name == DISCUSSION:
            featured = NodeCollectionFactory.resolve(DISCUSSION, ROW_VIEW, category='featured').get_card(context)
            latest = NodeCollectionFactory.resolve(DISCUSSION, ROW_VIEW, category='latest').get_card(context)
            return dict(featured=featured, latest=latest)
        elif self.model_name == EVENT:
            return dict(events_list=NodeCollectionFactory.resolve(EVENT, ROW_VIEW).get_card(context))
        else:
            raise Exception("not implemented")

class DetailPage(Page):

    def __init__(self, model_name):
        super(DetailPage, self).__init__(model_name)

    def get_context(self, context):
        if self.model_name == ACTIVITY:
            adventure_list = NodeCollectionFactory.resolve(ADVENTURE, GRID_VIEW).get_card(context)
            follower_list = NodeCollectionFactory.resolve(PROFILE, ROW_VIEW).get_card(context)
            discussion_list = NodeCollectionFactory.resolve(DISCUSSION, ROW_VIEW).get_card(context)
            article_list = NodeCollectionFactory.resolve(ARTICLE, GRID_VIEW).get_card(context)
            return dict(adventure_list=adventure_list, follower_list=follower_list, discussion_list=discussion_list, article_list=article_list)
        elif self.model_name == ADVENTURE:
            other_adventure_list = NodeCollectionFactory.resolve(ADVENTURE, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            advertisement_list = NodeCollectionFactory.resolve(ADVERTISEMENT, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            reviews = NodeCollectionFactory.resolve(POST, ROW_VIEW).get_card(context)
            return dict(other_adventure_list=other_adventure_list, advertisement_list=advertisement_list, reviews=reviews)
        elif self.model_name == PROFILE:
            wish_listed_adventure_list = NodeCollectionFactory.resolve(ADVENTURE, GRID_VIEW, category="wishlisted").get_card(context)
            accomplished_adventure_list = NodeCollectionFactory.resolve(ADVENTURE, GRID_VIEW, category="accomplished").get_card(context)
            following_list = NodeCollectionFactory.resolve(PROFILE, ROW_VIEW, category="following").get_card(context)
            follower_list = NodeCollectionFactory.resolve(PROFILE, ROW_VIEW, category="follower").get_card(context)
            discussion_list = NodeCollectionFactory.resolve(DISCUSSION, ROW_VIEW).get_card(context)
            article_list = NodeCollectionFactory.resolve(ARTICLE, GRID_VIEW).get_card(context)
            my_stream_list = NodeCollectionFactory.resolve(STREAM, ROW_VIEW, category='my').get_card(context)
            fitrangi_posts = NodeCollectionFactory.resolve(POST, GRID_VIEW, category="fitrangi").get_card(context)
            featured_profiles = ','.join(str(u.id) for u in profile_extractor.get_list("featured:bool|True;", False, 1, 10))
            return dict(wish_listed_adventure_list=wish_listed_adventure_list, accomplished_adventure_list=accomplished_adventure_list,
                            follower_list=follower_list, following_list=following_list, discussion_list=discussion_list,
                            article_list=article_list, my_stream_list=my_stream_list, fitrangi_posts=fitrangi_posts,
                            featured_profiles=featured_profiles)
        elif self.model_name == ARTICLE:
            comments = NodeCollectionFactory.resolve(POST, ROW_VIEW).get_card(context)
            related = NodeCollectionFactory.resolve(ARTICLE, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            advertisement_list = NodeCollectionFactory.resolve(ADVERTISEMENT, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            return dict(comments=comments, related=related, advertisement_list=advertisement_list)
        elif self.model_name == DISCUSSION:
            comments = NodeCollectionFactory.resolve(POST, ROW_VIEW).get_card(context)
            featured = NodeCollectionFactory.resolve(ARTICLE, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            advertisement_list = NodeCollectionFactory.resolve(ADVERTISEMENT, GRID_ROW_VIEW, is_scrollable=False).get_card(context)
            return dict(comments=comments, featured=featured, advertisement_list=advertisement_list)


explore_landing_page    = LandingPage('explore')
community_landing_page  = LandingPage('community')

article_search_page     = SearchPage(ARTICLE)
adventure_search_page   = SearchPage(ADVENTURE)
profile_search_page     = SearchPage(PROFILE)
discussion_search_page  = SearchPage(DISCUSSION)
event_search_page       = SearchPage(EVENT)

activity_detail_page    = DetailPage(ACTIVITY)
adventure_detail_page   = DetailPage(ADVENTURE)
profile_detail_page     = DetailPage(PROFILE)
article_detail_page     = DetailPage(ARTICLE)
discussion_detail_page  = DetailPage(DISCUSSION)