__author__ = 'arshad'

from app.models import update_content, Entity, ExternalNetwork, Charge, db, BookingEnquiry
from app.models.relationships import RelationShips
from app.models.profile import Profile
from app import utils

@update_content.apply
class Trip(Entity, ExternalNetwork, Charge, db.Document):
    starting_from = db.ReferenceField('Location')
    organizer = db.ReferenceField('Profile')
    activities = db.ListField(db.ReferenceField('Activity'))
    adventure = db.ReferenceField('Adventure')
    difficulty_rating = db.IntField()
    registration = db.StringField()
    start_date = db.DateTimeField()
    end_date = db.DateTimeField()
    schedule = db.ListField(db.StringField())
    things_to_carry = db.ListField(db.StringField())
    inclusive = db.ListField(db.StringField())
    exclusive = db.ListField(db.StringField())
    others = db.ListField(db.StringField())
    comments = db.ListField(db.ReferenceField('Post'))
    enquiries = db.ListField(db.EmbeddedDocumentField(BookingEnquiry))
    announcements = db.ListField(db.StringField())
    location = db.ReferenceField('Location')

    meta = {
        'indexes': [
            {'fields': ['-modified_timestamp', 'slug', 'name'], 'unique': False, 'sparse': False, 'types': False },
        ],
    }

    @property
    def duration(self):
        return (self.end_date - self.start_date).days

    @property
    def total_date(self):
        start_day = self.start_date.day
        start_sup = self._get_sup(self.start_date)
        start_month = utils.get_month(self.start_date.month)
        start_year = str(self.start_date.year)
        end_day = self.end_date.day
        end_sup = self._get_sup(self.end_date)
        end_month = utils.get_month(self.end_date.month)
        end_year = str(self.end_date.year)
        params = (start_day, start_sup, start_month, start_year, end_day, end_sup, end_month, end_year)
        if start_year == end_year:
            if start_month == end_month:
                _total_date = "%d<sup>%s</sup> - %d<sup>%s</sup> %s %s" % (start_day, start_sup, end_day, end_sup, end_month, end_year)
            else:
                _total_date = "%d<sup>%s</sup> %s - %d<sup>%s</sup> %s %s" % (start_day, start_sup, start_month, end_day, end_sup, end_month, end_year)
        else:
            _total_date = "%d<sup>%s</sup> %s %s - %d<sup>%s</sup> %s %s" % params
        return _total_date

    def _get_sup(self, date):
        if date.day is 1:
            return 'st'
        elif date.day is 2:
            return 'nd'
        elif date.day is 3:
            return 'rd'
        else:
            return 'th'

    def join_trip(self, profile):
        RelationShips.join(profile, self)

    def leave_trip(self, profile):
        RelationShips.unjoin(profile, self)

    def show_interest(self, profile):
        RelationShips.interested(profile, self)

    def loose_interest(self, profile):
        RelationShips.uninterested(profile, self)

    @property
    def interested(self):
        return [u for u in RelationShips.get_interested_in(self) if isinstance(u, Profile)]

    @property
    def joined(self):
        return [u for u in RelationShips.get_joined_in(self) if isinstance(u, Profile)]

    def add_enquiry(self, user, message):
        enquiry = BookingEnquiry(author=user, message=message)
        self.enquiries.append(enquiry)
        self.save()
