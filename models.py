from google.appengine.ext import db

class Process(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()

    def get_start_step(self):
        query = Step.all().filter('is_start', True)
        return query.get()

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
    def steps(self):
        return Step.all().filter('teams', self.key())

class Action(db.Model):
    process = db.ReferenceProperty(Process, collection_name='actions',
        required=True)
    name = db.StringProperty(required=True)
    incoming = db.ListProperty(db.Key)
    outgoing = db.ListProperty(db.Key)
    is_complete = db.BooleanProperty(default=False)

class Request(db.Expando):
    process = db.ReferenceProperty(Process, collection_name='requests',
        required=True)
    requestor = db.StringProperty(required=True)
    is_draft = db.BooleanProperty(default=False)

class Execution(db.Model):
    process = db.ReferenceProperty(Process, collection_name='executions',
        required=True)
    request = db.ReferenceProperty(Request, collection_name='executions',
        required=True)
    step = db.ReferenceProperty(Step, collection_name='executions',
        required=True)
    action = db.ReferenceProperty(Action, collection_name='executions')
    team = db.ReferenceProperty(Team, collection_name='executions')
    member = db.StringProperty(required=True)
    start_date = db.DateTimeProperty(auto_now_add=True)
    sent_date = db.DateTimeProperty()
    viewed_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    email_delay = db.IntegerProperty(default=0)
    action_delay = db.IntegerProperty(default=0)
    duration = db.IntegerProperty(default=0)