#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.runtime import apiproxy_errors

import utils

class Process(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()

    @property
    def id(self):
        """Return the unique ID for this process."""
        return self.key().id_or_name()

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
            logging.info('Deleting Action "%s" from datastore.' % action.id)
            entities.append(action)
            logging.info('Deleting Action "%s" from memcache.' % action.id)
            entity_keys.append(action.id)

        for step in self.steps:
            logging.info('Deleting Step "%s" from datastore.' % step.id)
            entities.append(step)
            logging.info('Deleting Step "%s" from memcache.' % step.id)
            entity_keys.append(step.id)

        if entities:
            try:
                db.delete(entities)
            except apiproxy_errors.CapabilityDisabledError:
                pass
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
            team = utils.load_from_cache(team_key, Team)
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


class Step(db.Model):
    process = db.ReferenceProperty(Process, collection_name='steps',
        required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    is_start = db.BooleanProperty(default=False)
    teams = db.ListProperty(db.Key)

    @property
    def id(self):
        """Return the unique ID for this step."""
        return self.key().id_or_name()

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

        process = utils.load_from_cache(process_key, Process)
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
            team = utils.load_from_cache(team_key, Team)
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
            team = utils.load_from_cache(team_key, Team)
            if isinstance(team, Team) and team.id not in data['teams']:
                data['teams'].append(team.id)
        if self.is_saved():
            data['key'] = self.id
        return data

class Team(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    members = db.ListProperty(basestring)

    @property
    def id(self):
        """Return the unique ID for this team."""
        return self.key().id_or_name()

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

class Action(db.Model):
    process = db.ReferenceProperty(Process, collection_name='actions',
        required=True)
    name = db.StringProperty(required=True)
    incoming = db.ListProperty(db.Key)
    outgoing = db.ListProperty(db.Key)
    is_complete = db.BooleanProperty(default=False)

    @property
    def id(self):
        """Return the unique ID for this action."""
        return self.key().id_or_name()

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

        process = utils.load_from_cache(process_key, Process)
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
            step = utils.load_from_cache(step_key, Step)
            if isinstance(step, Step) and step.key() not in step_keys:
                step_keys.append(step.key())
        if step_keys:
            action.incoming = step_keys

        # Parse outgoing step keys
        step_keys = []
        for step_key in data.get('outgoing'):
            step = utils.load_from_cache(step_key, Step)
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
            step = utils.load_from_cache(step_key, Step)
            if isinstance(step, Step) and step.id not in data['incoming']:
                data['incoming'].append(step.id)
        for step_key in self.outgoing:
            step = utils.load_from_cache(step_key, Step)
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
        """Return the unique ID for this execution."""
        return self.key().id_or_name()
