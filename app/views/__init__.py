from app.config import get_activities
from app.models.profile import Profile
from app import  app, cache

__author__ = 'arshad'



from functools import wraps
from flask import g, redirect, request, url_for, abort

from jinja2 import Environment, FileSystemLoader
from app.settings import TEMPLATE_FOLDER

env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))

@app.before_request
def setup_user():
    if session.get('user') is not None:
        g.user = Profile.objects(pk=session['user']).first()

def force_setup_context(context={}):
    user = g.user if hasattr(g, 'user') and g.user is not None else None
    d = dict(user=user, menu=get_menu_selection(request.path))
    if user:
        context['public_activity_count'] = user.public_activity_count if user.public_activity_count else 0
        context['private_activity_count'] = user.private_activity_count if user.private_activity_count else 0
    for k, v in d.iteritems():
        context[k] = v
    return context


@app.context_processor
def setup_context():
    user = g.user if hasattr(g, 'user') and g.user is not None else None
    return dict(user=user, menu=get_menu_selection(request.path))

#@cache.cached(timeout=3600 * 24)
def get_menu_selection(request_path):
    top, main, inner = None, None, None

    menu_args = [
        ('/activity', ('explore', 'activity')),
        ('/adventure', ('explore', 'adventure')),
        ('/article', ('explore', 'journal')),
        ('/blog', ('explore', 'journal')),
        ('/journal', ('explore', 'journal')),
        ('/profile', ('community', 'profile')),
        ('/discussion', ('community', 'discussion')),
        ('/event', ('community', 'event')),
        ('/trip', ('trip', None)),
        ('/explore', ('explore', None)),
        ('/community', ('community', None))
    ]

    for k, v in menu_args:
        if k in request.path:
            top, main = v
            break

    if '/activity' in request_path:
        inner = request.args.get('name', None)




    menu = Menu(top, main, inner)
    return menu

class Menu(object):
    def __init__(self, top, main, inner):
        self.app_name = top
        self.main_menu = main
        self.inner = inner

    def __repr__(self):
        return "%s -> %s -> %s" % (self.app_name, self.main_menu, self.inner)


from .common import *
from .messaging import *