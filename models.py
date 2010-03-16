#
# Copyright 2010 Flomosa, LLC
#

import logging

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

class Process(FlomosaBase):
    name = db.StringProperty(required=True)
    description = db.TextProperty()

    def delete(self):
        """Delete the process from the datastore and memcache.

        This also deletes and actions and steps created under this process.
        """
        self.delete_steps_actions()
        return cache.delete_from_cache(self)

    @classmethod
    def from_dict(cls, data):
        """Return a new Process instance from a dict object."""

        if not data or not isinstance(data, dict):
            return None

        process_key = data.get('key', utils.generate_key())
        kind = data.get('kind', None)
        name = data.get('name', None)
        description = data.get('description', None)

        if not name:
            raise KeyError('Missing "name" parameter.')
        if not kind:
            raise KeyError('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise ValueError('Expected "kind=%s", found "kind=%s".' % \
                (cls.__name__, kind))

        process = cls.get_or_insert(process_key, name=name)
        process.name = name

        if description is not None:
            process.description = description
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

        found_member = False
        for team_key in step.teams:
            team = Team.get(team_key)
            if not team:
                continue
            elif not team.members:
                logging.error('No team members found in team "%s"' % team.id)
                continue
            else:
                found_member = True
                break
        return found_member

    def to_dict(self):
        """Return process as a dict object."""

        data = {
            'kind': self.kind(),
            'name': self.name,
            'description': self.description
        }
        if self.is_saved():
            data['key'] = self.id
        data['steps'] = [step.to_dict() for step in self.steps]
        data['actions'] = [action.to_dict() for action in self.actions]
        return data


class Step(FlomosaBase):
    process = db.ReferenceProperty(Process, collection_name='steps',
        required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    is_start = db.BooleanProperty(default=False)
    teams = db.ListProperty(db.Key)

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
        teams = data.get('teams', None)

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

        step = cls.get_or_insert(step_key, process=process, name=name)
        step.process = process
        step.name = name

        if description is not None:
            step.description = description
        if is_start is not None:
            step.is_start = bool(is_start)
        team_keys = []
        for team_key in teams:
            team = Team.get(team_key)
            if isinstance(team, Team) and team.key() not in team_keys:
                team_keys.append(team.key())
        if team_keys:
            step.teams = team_keys

        return step

    def to_dict(self):
        """Return step as a dict object."""

        data = {
            'kind': self.kind(),
            'name': self.name,
            'process': self.process.id,
            'description': self.description,
            'is_start': bool(self.is_start),
            'teams': []
        }
        for team_key in self.teams:
            team = Team.get(team_key)
            if isinstance(team, Team) and team.id not in data['teams']:
                data['teams'].append(team.id)
        if self.is_saved():
            data['key'] = self.id
        return data

    def queue_tasks(self, request):
        """Queue execution tasks for a given request."""

        if not isinstance(request, Request):
            return None

        queue = taskqueue.Queue('request-process')
        for team_key in self.teams:
            team = Team.get(team_key)
            if not team:
                continue

            for member in team.members:
                execution_key = utils.generate_key()

                execution = Execution(key_name=execution_key,
                    process=self.process, request=request, step=self,
                    team=team, member=member)

                try:
                    execution.put()
                except Exception, e:
                    logging.error(e)
                    continue

                logging.info('Queuing: (member="%s") (team="%s") (step="%s") ' \
                    '(process="%s")' % (member, team.name, self.name,
                    self.process.name))
                task = taskqueue.Task(params={'key': execution.id})
                queue.add(task)

class Team(FlomosaBase):
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    members = db.ListProperty(basestring)

    @property
    def steps(self):
        """Return the steps this team belongs to."""
        return Step.all().filter('teams', self.key())

    @classmethod
    def from_dict(cls, data):
        """Return a new Team instance from a dict object."""

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

        team = cls.get_or_insert(team_key, name=name)
        team.name = name

        if description is not None:
            team.description = description
        if isinstance(members, list):
            team.members = members
        return team

    def to_dict(self):
        """Return process as a dict object."""

        data = {
            'kind': self.kind(),
            'name': self.name,
            'description': self.description,
            'members': self.members
        }
        if self.is_saved():
            data['key'] = self.id
        return data

class Action(FlomosaBase):
    process = db.ReferenceProperty(Process, collection_name='actions',
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
            if isinstance(step, Step) and step.key() not in step_keys:
                step_keys.append(step.key())
        if step_keys:
            action.incoming = step_keys

        # Parse outgoing step keys
        step_keys = []
        for step_key in data.get('outgoing'):
            step = Step.get(step_key)
            if isinstance(step, Step) and step.key() not in step_keys:
                step_keys.append(step.key())
        if step_keys:
            action.outgoing = step_keys

        return action

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
            if isinstance(step, Step) and step.id not in data['incoming']:
                data['incoming'].append(step.id)
        for step_key in self.outgoing:
            step = Step.get(step_key)
            if isinstance(step, Step) and step.id not in data['outgoing']:
                data['outgoing'].append(step.id)
        return data

class Request(db.Expando):
    process = db.ReferenceProperty(Process, collection_name='requests',
        required=True)
    requestor = db.EmailProperty(required=True)
    contact = db.EmailProperty()
    is_draft = db.BooleanProperty(default=False)

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
    queued_for_send = db.BooleanProperty(default=False)
    sent_date = db.DateTimeProperty()
    viewed_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    email_delay = db.IntegerProperty(default=0) # viewed_date-sent_date
    action_delay = db.IntegerProperty(default=0) # end_date-viewed_date
    duration = db.IntegerProperty(default=0) # end_date-start_date

class Consumer(db.Model):
    oauth_token = db.StringProperty(required=True)
    oauth_secret = db.StringProperty(required=True)
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    email_address = db.EmailProperty(required=True)
    password = db.StringProperty(required=True)
    created_date = db.DateTimeProperty(auto_now_add=True)
