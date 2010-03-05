#
# Copyright 2010 Flomosa, LLC
#

from google.appengine.ext import db
import utils

class Process(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()

    @property
    def id(self):
        return self.key().id_or_name()

    def get_start_step(self):
        query = Step.all().filter('is_start', True)
        return query.get()

    def is_valid(self):
        step = self.get_start_step()
        if not step:
            return False

        found_member = False
        for team_key in step.teams:
            team = utils.load_from_cache(team_key, Team)
            if not team:
                continue
            elif not team.members:
                logging.error('No team members found in team "%s"' % \
                    team_key.name())
                continue
            else:
                found_member = True
                break
        return found_member

    def to_dict(self):
        data = dict(name=self.name, description=self.description)
        if self.is_saved():
            data['id'] = self.id
        return data

    def to_dot(self):
        name = self.name.replace(' ', '_')

        nodes = ''
        for step in self.steps:
            nodes += '%s [label="%s"]\n' % (step.key(), step.name)
        nodes += 'finish [label="Finish"]\n'

        actions = ''
        for action in self.actions:
            for incoming in action.incoming:
                if action.is_complete:
                    actions += '%s -> finish [label="%s"]\n' % (incoming,
                        action.name)
                else:
                    for outgoing in action.outgoing:
                        actions += '%s -> %s [label="%s"]\n' % (incoming,
                            outgoing, action.name)

        return 'digraph %s {\n%s\n%s}' % (name, nodes, actions)

class Step(db.Model):
    process = db.ReferenceProperty(Process, collection_name='steps',
        required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    is_start = db.BooleanProperty(default=False)
    teams = db.ListProperty(db.Key)

    @property
    def id(self):
        return self.key().id_or_name()

    @property
    def actions(self):
        return Action.all().filter('incoming', self.key())

    @property
    def prior(self):
        return Action.all().filter('outgoing', self.key())

class Team(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    members = db.ListProperty(basestring)

    @property
    def id(self):
        return self.key().id_or_name()

    @property
    def steps(self):
        return Step.all().filter('teams', self.key())

class Action(db.Model):
    process = db.ReferenceProperty(Process, collection_name='actions',
        required=True)
    name = db.StringProperty(required=True)
    incoming = db.ListProperty(db.Key)
    outgoing = db.ListProperty(db.Key)
    is_complete = db.BooleanProperty(default=False)

    @property
    def id(self):
        return self.key().id_or_name()

class Request(db.Expando):
    process = db.ReferenceProperty(Process, collection_name='requests',
        required=True)
    requestor = db.EmailProperty(required=True)
    contact = db.EmailProperty()
    is_draft = db.BooleanProperty(default=False)

    @property
    def id(self):
        return self.key().id_or_name()

    def to_dict(self):
        data = dict(process=self.process.id,
            requestor=self.requestor, is_draft=self.is_draft)
        for property in self.dynamic_properties():
            data[property] = getattr(self, property)

        if self.is_saved():
            data['id'] = self.id
        return data

class Execution(db.Model):
    process = db.ReferenceProperty(Process, collection_name='executions',
        required=True)
    request = db.ReferenceProperty(Request, collection_name='executions',
        required=True)
    step = db.ReferenceProperty(Step, collection_name='executions',
        required=True)
    action = db.ReferenceProperty(Action, collection_name='executions')
    team = db.ReferenceProperty(Team, collection_name='executions')
    member = db.EmailProperty(required=True)
    start_date = db.DateTimeProperty(auto_now_add=True)
    sent_date = db.DateTimeProperty()
    viewed_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    email_delay = db.IntegerProperty(default=0) # viewed_date-sent_date
    action_delay = db.IntegerProperty(default=0) # end_date-viewed_date
    duration = db.IntegerProperty(default=0) # end_date-start_date

    @property
    def id(self):
        return self.key().id_or_name()