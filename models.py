#
# Copyright 2010 Flomosa, LLC
#

import logging
import datetime

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.runtime import apiproxy_errors

import utils
import cache


class FlomosaBase(db.Model):
    """Base model inherited by other models."""

    @property
    def id(self):
        """Return the unique ID for this model."""
        return self.key().id_or_name()

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.__unicode__()

    @classmethod
    def get(cls, key):
        """Lookup the model in memcache and then the datastore."""
        return cache.get_from_cache(cls, key)

    def put(self):
        """Save the model to the datastore and memcache."""
        return cache.save_to_cache(self)

    def delete(self):
        """Delete the model from the datastore and memcache."""
        return cache.delete_from_cache(self)


class Client(FlomosaBase):
    oauth_secret = db.StringProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    company = db.StringProperty()
    email_address = db.EmailProperty(required=True)
    password = db.StringProperty(required=True)
    created_date = db.DateTimeProperty(auto_now_add=True)

    @property
    def secret(self):
        return self.oauth_secret

    def to_dict(self):
        """Return client as a dict object."""

        data = {
            'kind': self.kind(),
            'oauth_secret': self.oauth_secret,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company': self.company,
            'email_address': self.email_address,
            'password': self.password,
            'created_date': self.created_date
        }
        if self.is_saved():
            data['key'] = self.id
        return data


class Team(FlomosaBase):
    client = db.ReferenceProperty(Client,
        collection_name='teams',
        required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    members = db.ListProperty(basestring)

    @classmethod
    def from_dict(cls, client, data):
        """Return a new Team instance from a dict object."""

        if not client or not isinstance(client, Client):
            return None

        if not data or not isinstance(data, dict):
            return None

        team_key = data.get('key', utils.generate_key())
        kind = data.get('kind', None)
        name = data.get('name', None)
        description = data.get('description', None)
        members = data.get('members', None)

        if not name:
            raise KeyError('Missing "name" parameter.')
        if not kind:
            raise KeyError('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise ValueError('Expected "kind=%s", found "kind=%s".' % \
                (cls.__name__, kind))

        team = cls.get_by_key_name(team_key)
        if not team:
            team = cls(key_name=team_key,
                client=client,
                name=name)
        elif team.client.id != client.id:
            raise ValueError('Permission Denied.')
        else:
            team.name = name

        if description is not None:
            team.description = description
        if isinstance(members, list):
            team.members = members
        return team

    def to_dict(self):
        """Return team as a dict object."""

        data = {
            'kind': self.kind(),
            'name': self.name,
            'description': self.description,
            'members': self.members
        }
        if self.is_saved():
            data['key'] = self.id
        return data


class Process(FlomosaBase):
    client = db.ReferenceProperty(Client,
        collection_name='processes',
        required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    collect_stats = db.BooleanProperty(default=False)

    def put(self):
        """Saves the process to the datastore and memcache.

        If the process is not collecting statistics, delete any stored
        statistics from the datastore.
        """

        if not self.collect_stats:
            self.delete_stats()

        return cache.save_to_cache(self)

    def delete(self):
        """Delete the process from the datastore and memcache.

        Also deletes and actions and steps created under this process and
        any collected statistics.
        """

        self.delete_stats()
        self.delete_steps_actions()
        return cache.delete_from_cache(self)

    def add_step(self, name, description=None, team=None, members=[],
            is_start=True, key=None):
        """Add a step to this process."""

        for step in self.steps:
            is_start = False
            break
        if key is None:
            key = utils.generate_key()
        step = Step(key_name=key,
            process=self,
            name=name)
        step.is_start = bool(is_start)
        step.team = team
        step.members = members
        step.description = description

        try:
            step.put()
        except Exception, e:
            raise e
        return step

    def delete_stats(self):
        """Delete any statistic objects for this Process."""
        for stats in self.stats:
            try:
                stats.delete()
            except Exception, e:
                logging.error('Unable to delete Statistcs object for ' \
                    'Process "%s" from datastore.' % self.id)

    @classmethod
    def from_dict(cls, client, data):
        """Return a new Process instance from a dict object."""

        if not client or not isinstance(client, Client):
            return None

        if not data or not isinstance(data, dict):
            return None

        process_key = data.get('key', utils.generate_key())
        kind = data.get('kind', None)
        name = data.get('name', None)
        description = data.get('description', None)
        collect_stats = data.get('collect_stats', None)

        if not name:
            raise KeyError('Missing "name" parameter.')
        if not kind:
            raise KeyError('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise ValueError('Expected "kind=%s", found "kind=%s".' % \
                (cls.__name__, kind))

        process = cls.get_by_key_name(process_key)
        if not process:
            process = cls(key_name=process_key,
                client=client,
                name=name)
        elif process.client.id != client.id:
            raise ValueError('Permission Denied.')
        else:
            process.name = name

        if description is not None:
            process.description = description
        if collect_stats is not None:
            process.collect_stats = collect_stats
        return process

    def delete_steps_actions(self):
        """Delete this process' steps and actions."""

        entities = []
        entity_keys = []

        for action in self.actions:
            logging.debug('Deleting Action "%s" from datastore.' % action.id)
            entities.append(action)
            logging.debug('Deleting Action "%s" from memcache.' % action.id)
            entity_keys.append(action.id)

        for step in self.steps:
            logging.debug('Deleting Step "%s" from datastore.' % step.id)
            entities.append(step)
            logging.debug('Deleting Step "%s" from memcache.' % step.id)
            entity_keys.append(step.id)

        if entities:
            try:
                db.delete(entities)
            except apiproxy_errors.CapabilityDisabledError:
                logging.error('Unable to delete steps and actions from ' \
                    'Process "%s" due to maintenance.' % self.id)
        if entity_keys:
            memcache.delete_multi(entity_keys)

    def get_start_step(self):
        """Get start step in this process."""

        query = Step.all().filter('is_start', True)
        return query.get()

    def is_valid(self):
        """Is this process valid?

        - Must have a start step defined
        - Must be at least one team member and team assigned to the start step
        """

        step = self.get_start_step()
        if not step:
            return False

        if step.members:
            return True
        if step.team and isinstance(step.team, Team):
            if step.team.members:
                return True

        logging.error('No team members found in step "%s"' % step.id)
        return False

    def to_dict(self):
        """Return process as a dict object."""

        data = {
            'kind': self.kind(),
            'name': self.name,
            'description': self.description,
            'collect_stats': self.collect_stats
        }
        if self.is_saved():
            data['key'] = self.id
        data['steps'] = [step.to_dict() for step in self.steps]
        data['actions'] = [action.to_dict() for action in self.actions]
        return data


class Step(FlomosaBase):
    process = db.ReferenceProperty(Process,
        collection_name='steps',
        required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    is_start = db.BooleanProperty(default=False)
    team = db.ReferenceProperty(Team,
        collection_name='steps')
    members = db.ListProperty(basestring)

    @property
    def actions(self):
        """Return the actions that come after this step."""
        return Action.all().filter('incoming', self.key())

    @property
    def prior(self):
        """Return the actions that come before this step."""
        return Action.all().filter('outgoing', self.key())

    @classmethod
    def from_dict(cls, data):
        """Return a new Step instance from a dict object."""

        if not data or not isinstance(data, dict):
            return None

        step_key = data.get('key', utils.generate_key())
        kind = data.get('kind', None)
        process_key = data.get('process', None)
        name = data.get('name', None)
        description = data.get('description', None)
        is_start = data.get('is_start', None)
        team_key = data.get('team', None)
        members = data.get('members', None)

        if not name:
            raise KeyError('Missing "name" parameter.')
        if not kind:
            raise KeyError('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise ValueError('Expected "kind=%s", found "kind=%s".' % \
                (cls.__name__, kind))
        if not process_key:
            raise KeyError('Missing "process" parameter.')

        process = Process.get(process_key)
        if not process:
            raise ValueError('Process key "%s" does not exist.' % process_key)

        step = cls.get_or_insert(step_key,
            process=process,
            name=name)
        step.process = process
        step.name = name

        if description is not None:
            step.description = description
        if is_start is not None:
            step.is_start = bool(is_start)
        if isinstance(members, list):
            step.members = members
        if team_key is not None:
            team = Team.get(team_key)
            if team and isinstance(team, Team):
                step.team = team

        return step

    def add_action(self, name, next_step=None, is_complete=False, key=None):
        """Add an action after this step."""

        if key is None:
            key = utils.generate_key()

        action = Action(key_name=key,
            process=self.process,
            name=name)
        action.is_complete = is_complete
        action.add_incoming_step(self)
        if next_step and isinstance(next_step, Step):
            action.add_outgoing_step(next_step)

        try:
            action.put()
        except Exception, e:
            raise e
        return action

    def to_dict(self):
        """Return step as a dict object."""

        data = {
            'kind': self.kind(),
            'name': self.name,
            'process': self.process.id,
            'description': self.description,
            'is_start': bool(self.is_start),
            'members': self.members
        }
        if self.team:
            data['team'] = self.team.id
        else:
            data['team'] = None
        if self.is_saved():
            data['key'] = self.id
        return data

    def _create_execution(self, request, member, team=None):
        """Create an execution object for a given member."""

        execution_key = utils.generate_key()

        execution = Execution(key_name=execution_key,
            process=self.process,
            request=request,
            step=self,
            member=member)
        if team and isinstance(team, Team):
            execution.team = team

        try:
            execution.put()
        except Exception, e:
            logging.error(e)
            return None

        return execution.id

    def queue_tasks(self, request):
        """Queue execution tasks for a given request."""

        if not isinstance(request, Request):
            return None
        if not self.team and not self.members:
            return None

        tasks = []
        if self.team:
            for member in self.team.members:
                execution_key = self._create_execution(request, member,
                    self.team)

                if execution_key:
                    logging.info('Queuing: (member="%s") (team="%s") ' \
                        '(step="%s") (process="%s")' % (member, self.team.name,
                        self.name, self.process.name))
                    task = taskqueue.Task(params={'key': execution_key})
                    tasks.append(task)
        if self.members:
            for member in self.members:
                execution_key = self._create_execution(request, member)

                if execution_key:
                    logging.info('Queuing: (member="%s") (team=None) ' \
                        '(step="%s") (process="%s")' % (member, self.name,
                        self.process.name))
                    task = taskqueue.Task(params={'key': execution_key})
                    tasks.append(task)
        if tasks:
            queue = taskqueue.Queue('request-process')
            queue.add(tasks)
        return None


class Action(FlomosaBase):
    process = db.ReferenceProperty(Process,
        collection_name='actions',
        required=True)
    name = db.StringProperty(required=True)
    incoming = db.ListProperty(db.Key)
    outgoing = db.ListProperty(db.Key)
    is_complete = db.BooleanProperty(default=False)

    @classmethod
    def from_dict(cls, data):
        """Return a new Action instance from a dict object."""

        if not data or not isinstance(data, dict):
            return None

        action_key = data.get('key', utils.generate_key())
        kind = data.get('kind', None)
        name = data.get('name', None)
        is_complete = data.get('is_complete', None)

        if not name:
            raise KeyError('Missing "name" parameter.')
        if not kind:
            raise KeyError('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise ValueError('Expected "kind=%s", found "kind=%s".' % \
                (cls.__name__, kind))
        try:
            process_key = data['process']
        except KeyError:
            raise KeyError('Missing "process" parameter.')

        process = Process.get(process_key)
        if not process:
            raise ValueError('Process key "%s" does not exist.' % process_key)

        action = cls.get_or_insert(action_key, process=process, name=name)
        action.process = process
        action.name = name

        if is_complete is not None:
            action.is_complete = bool(is_complete)

        # Parse incoming step keys
        step_keys = []
        for step_key in data.get('incoming'):
            step = Step.get(step_key)
            if step and isinstance(step, Step) and step.key() not in step_keys:
                step_keys.append(step.key())
        if step_keys:
            action.incoming = step_keys

        # Parse outgoing step keys
        step_keys = []
        for step_key in data.get('outgoing'):
            step = Step.get(step_key)
            if step and isinstance(step, Step) and step.key() not in step_keys:
                step_keys.append(step.key())
        if step_keys:
            action.outgoing = step_keys

        return action

    def add_incoming_step(self, step):
        """Add an incoming Step to this Action."""
        if not isinstance(step, Step):
            raise ValueError('Must be a valid Step instance.')
        self.incoming.append(step.key())

    def add_outgoing_step(self, step):
        """Add an outgoing Step to this Action."""
        if not isinstance(step, Step):
            raise ValueError('Must be a valid Step instance.')
        self.is_complete = False
        self.outgoing.append(step.key())

    def to_dict(self):
        """Return action as a dict object."""

        data = {
            'kind': self.kind(),
            'process': self.process.id,
            'name': self.name,
            'is_complete': bool(self.is_complete),
            'incoming': [],
            'outgoing': []
        }
        if self.is_saved():
            data['key'] = self.id
        for step_key in self.incoming:
            step = Step.get(step_key)
            if step and isinstance(step, Step) and step.id not in \
                data['incoming']:
                data['incoming'].append(step.id)
        for step_key in self.outgoing:
            step = Step.get(step_key)
            if step and isinstance(step, Step) and step.id not in \
                data['outgoing']:
                data['outgoing'].append(step.id)
        return data


class Request(db.Expando):
    client = db.ReferenceProperty(Client,
        collection_name='requests',
        required=True)
    process = db.ReferenceProperty(Process,
        collection_name='requests',
        required=True)
    requestor = db.EmailProperty(required=True)
    contact = db.EmailProperty()
    is_draft = db.BooleanProperty(default=False)
    submitted_date = db.DateTimeProperty(auto_now_add=True)
    is_completed = db.BooleanProperty(default=False)
    completed_date = db.DateTimeProperty()
    duration = db.IntegerProperty(default=0)

    @property
    def id(self):
        """Return the unique ID for this request."""
        return self.key().id_or_name()

    @classmethod
    def get(cls, key):
        """Lookup the request key in memcache and then the datastore."""
        return cache.get_from_cache(cls, key)

    def put(self):
        """Save the Request to the datastore and memcache."""
        return cache.save_to_cache(self)

    def delete(self):
        """Delete the Request from the datastore and memcache."""
        return cache.delete_from_cache(self)

    def set_completed(self, completed_date=None):
        """Set the request has being completed."""

        if self.is_completed:
            return None

        # If we haven't already marked this request as being
        # completed, set the is_completed flag and compute
        # the duration the request was in progress, in seconds.

        self.is_completed = True
        if not completed_date:
            completed_date = datetime.datetime.now()
        self.completed_date = completed_date
        if self.submitted_date:
            delta = self.completed_date - self.submitted_date
            self.duration = delta.days * 86400 + delta.seconds

        return self.put()

    def get_submitted_data(self):
        """Return a dict of the dynamic properties of this request."""

        data = {}
        for property in self.dynamic_properties():
            data[property] = str(getattr(self, property))
        return data

    def get_executions(self):
        """Return executions in creation order.
        # TODO
        """
        pass

    def to_dict(self):
        """Return request as a dict object."""

        data = {
            'kind': self.kind(),
            'process': self.process.id,
            'requestor': self.requestor,
            'contact': self.contact,
            'is_draft': self.is_draft
        }
        for property in self.dynamic_properties():
            data[property] = getattr(self, property)
        if self.is_saved():
            data['key'] = self.id
        return data


class Execution(FlomosaBase):
    process = db.ReferenceProperty(Process,
        collection_name='executions',
        required=True)
    request = db.ReferenceProperty(Request,
        collection_name='executions',
        required=True)
    step = db.ReferenceProperty(Step,
        collection_name='executions',
        required=True)
    action = db.ReferenceProperty(Action,
        collection_name='executions')
    team = db.ReferenceProperty(Team,
        collection_name='executions')
    member = db.EmailProperty(required=True)
    start_date = db.DateTimeProperty(auto_now_add=True)
    queued_for_send = db.BooleanProperty(default=False)
    reminder_count = db.IntegerProperty(default=0)
    last_reminder_sent_date = db.DateTimeProperty()
    sent_date = db.DateTimeProperty()
    viewed_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    email_delay = db.IntegerProperty(default=0) # viewed_date-sent_date
    action_delay = db.IntegerProperty(default=0) # end_date-viewed_date
    duration = db.IntegerProperty(default=0) # end_date-start_date

    def set_completed(self, action, end_date=None):
        """Set this execution as being completed."""

        if not action or not isinstance(action, Action):
            raise Exception('No action specified')

        self.action = action
        if not end_date:
            end_date = datetime.datetime.now()
        self.end_date = end_date
        if self.viewed_date and not self.action_delay:
            delta = self.end_date - self.viewed_date
            self.action_delay = delta.days * 86400 + delta.seconds
        if self.start_date and not self.duration:
            delta = self.end_date - self.start_date
            self.duration = delta.days * 86400 + delta.seconds

        return self.put()

    def is_step_completed(self):
        """Has this request step been completed by anyone?"""

        query = self.all()
        query.filter('step =', self.step)
        query.filter('request =', self.request)
        query.filter('member !=', self.member)
        query.order('member')
        query.order('end_date')

        results = query.fetch(30)

        for execution in results:
            if execution.action:
                return execution
        return None

    def num_passes(self, limit=5):
        """Return number of times through this step for this request."""

        query = self.all()
        query.filter('step =', self.step)
        query.filter('request =', self.request)
        query.filter('member =', self.member)
        return query.count(limit)


class Statistic(db.Model):
    process = db.ReferenceProperty(Process,
        collection_name='stats')
    date_key = db.StringProperty(required=True)
    type = db.StringProperty(required=True)
    year = db.IntegerProperty(required=True)
    month = db.IntegerProperty()
    week_num = db.IntegerProperty()
    num_requests = db.IntegerProperty(default=0)
    num_requests_completed = db.IntegerProperty(default=0)
    min_request_seconds = db.IntegerProperty(default=0) # seconds
    max_request_seconds = db.IntegerProperty(default=0) # seconds
    avg_request_seconds = db.FloatProperty(default=0.0) # seconds
    total_request_seconds = db.IntegerProperty(default=0) # seconds

    @property
    def id(self):
        return '%s_%s' % (self.process.id, self.date_key)

    def log(self, request):
        """Store request data in a Statistic object.

        Executed when a request has been completed.
        """

        if request.duration > 0:
            if self.min_request_seconds == 0:
                self.min_request_seconds = request.duration
            elif request.duration < self.min_request_seconds:
                self.min_request_seconds = request.duration
            if request.duration > self.max_request_seconds:
                self.max_request_seconds = request.duration
            self.num_requests_completed += 1
            self.total_request_seconds += request.duration
            self.avg_request_seconds = float(self.total_request_seconds /
                self.num_requests_completed)
        else:
            self.num_requests += 1

    @classmethod
    def get_bucket(cls, process, type='daily', date_key=None):
        """Get or create a Statistics object for a Process."""

        if not process and not isinstance(process, Process):
            return None

        valid_types = ('daily', 'weekly', 'monthly', 'yearly')
        if type not in valid_types:
            return None

        today = datetime.date.today()
        month = None
        week_num = None
        if date_key is None:
            if type == 'daily':
                date_key = '%d%02d%02d' % (today.year, today.month, today.day)
                month = today.month
                week_num = today.isocalendar()[1]
            elif type == 'weekly':
                week_num = today.isocalendar()[1]
                date_key = '%dW%02d' % (today.year, week_num)
            elif type == 'monthly':
                date_key = '%d%02d' % (today.year, today.month)
                month = today.month
            elif type == 'yearly':
                date_key = today.year
                week_num = None
            else:
                return None
            date_key = str(date_key)

        stats_key = '%s_%s' % (process.id, date_key)

        stats = cls.get_or_insert(stats_key,
            process=process,
            date_key=date_key,
            type=type,
            year=today.year)
        stats.process = process
        stats.date_key = date_key
        stats.type = type
        stats.year = today.year
        stats.month = month
        stats.week_num = week_num
        return stats

    @classmethod
    def store_stats(cls, request, process):
        """Log the Request statistics in a Process.

        This will create daily, weekly, monthly and yearly statistics objects
        for the given Process and record the request in those buckets.
        """

        if not isinstance(request, Request):
            logging.error('No Request object found')
            return None
        if not isinstance(process, Process):
            logging.error('No Process object found')
            return None

        daily = cls.get_bucket(process, 'daily')
        weekly = cls.get_bucket(process, 'weekly')
        monthly = cls.get_bucket(process, 'monthly')
        yearly = cls.get_bucket(process, 'yearly')

        buckets = []
        buckets.append(daily)
        buckets.append(weekly)
        buckets.append(monthly)
        buckets.append(yearly)

        for bucket in buckets:
            if bucket:
                bucket.log(request)

                try:
                    bucket.put()
                except Exception, e:
                    logging.warning('Unable to save Statistic object "%s".' \
                        % bucket.id)

    def to_dict(self):
        """Return statistics as a dict object."""

        data = {
            'kind': self.kind(),
            'process': self.process.id,
            'date_key': self.date_key,
            'type': self.type,
            'num_requests': self.num_requests,
            'num_requests_completed': self.num_requests_completed,
            'min_request_seconds': self.min_request_seconds,
            'max_request_seconds': self.max_request_seconds,
            'avg_request_seconds': self.avg_request_seconds,
            'total_request_seconds': self.total_request_seconds
        }
        if self.is_saved():
            data['key'] = self.id
        return data
