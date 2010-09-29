#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import datetime
import logging

from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.runtime import apiproxy_errors

from flomosa import cache, exceptions, settings, utils


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
    def get(cls, key, client=None):
        """Lookup the model in memcache and then the datastore."""
        model = cache.get_from_cache(cls, key)
        if client and client.id != model.client.id:
            raise exceptions.UnauthorizedException('Client "%s" is not ' \
                'authorized to access %s "%s".' % (client.id, model.kind(),
                                                   model.id))
        return model

    def put(self):
        """Save the model to the datastore and memcache."""
        model = cache.save_to_cache(self)
        if model:
            return model.key()
        return None

    def delete(self):
        """Delete the model from the datastore and memcache."""
        return cache.delete_from_cache(self)


class Hub(db.Model):
    """PubSubHubBub hub URL listing."""

    url = db.LinkProperty() # http://pubsubhubbub.appspot.com

    def __unicode__(self):
        return unicode(self.hub_url)

    def __str__(self):
        return self.__unicode__()


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
            'created_date': str(self.created_date)
        }
        if self.is_saved():
            data['key'] = self.id
        return data


class Team(FlomosaBase):
    client = db.ReferenceProperty(Client, collection_name='teams',
                                  required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    members = db.ListProperty(basestring)

    def get_absolute_url(self):
        url = '%s/teams/%s.json' % (settings.HTTPS_URL, self.id)
        return url

    @classmethod
    def from_dict(cls, client, data):
        """Return a new Team instance from a dict object."""

        if not (client and isinstance(client, Client)):
            raise exceptions.MissingException('No client found')

        if not (data and isinstance(data, dict)):
            raise exceptions.MissingException('No data found')

        kind = data.get('kind', None)
        name = data.get('name', None)

        if not name:
            raise exceptions.MissingException('Missing "name" parameter.')
        if not kind:
            raise exceptions.MissingException('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise exceptions.MissingException('Expected "kind=%s", found ' \
                '"kind=%s".' % (cls.__name__, kind))

        team_key = data.get('key', None)
        if not team_key:
            team_key = utils.generate_key()
        description = data.get('description', None)
        members = data.get('members', None)

        team = cls.get_or_insert(team_key, client=client, name=name)
        team.description = description
        team.members = members or []
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
    client = db.ReferenceProperty(Client, collection_name='processes',
                                  required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    collect_stats = db.BooleanProperty(default=False)

    def get_absolute_url(self):
        url = '%s/processes/%s.json' % (settings.HTTPS_URL, self.id)
        return url

    def put(self):
        """Saves the process to the datastore and memcache.

        If the process is not collecting statistics, delete any stored
        statistics from the datastore.
        """

        if self.is_saved() and not self.collect_stats:
            self.delete_stats()

        process = cache.save_to_cache(self)
        if process:
            return process.key()
        return None

    def delete(self):
        """Delete the process from the datastore and memcache.

        Also deletes and actions and steps created under this process and
        any collected statistics.
        """

        self.delete_stats()
        self.delete_steps_actions()
        return cache.delete_from_cache(self)

    def add_steps(self, steps):
        "Add multiple steps to this process."
        for data in steps:
            kwargs = {'step_key': data.get('key'),
                      'members': data.get('members'),
                      'team_key': data.get('team'),
                      'description': data.get('description'),
                      'is_start': data.get('is_start')}
            self.add_step(data['name'], **kwargs)

    def add_step(self, name, description=None, team_key=None,
                 members=None, is_start=None, step_key=None):
        """Add a step to this process."""

        if is_start is None:
            is_start = True
            for step in self.steps:
                is_start = False
                break
        if not members:
            members = []
        if not step_key:
            step_key = utils.generate_key()

        step = Step.get_by_key_name(step_key, parent=self)
        if not step:
            step = Step(key_name=step_key, parent=self, process=self, name=name)
        step.is_start = bool(is_start)
        if team_key:
            team = Team.get(team_key)
            if team:
                step.team = team
        step.members = members
        step.description = description
        step.put()
        return step

    def add_actions(self, actions):
        """Add multiple actions to this process."""
        for data in actions:
            kwargs = {'incoming': data.get('incoming'),
                      'outgoing': data.get('outgoing'),
                      'action_key': data.get('key'),
                      'is_complete': data.get('is_complete')}
            self.add_action(data['name'], **kwargs)

    def add_action(self, name, incoming=None, outgoing=None, is_complete=False,
                   action_key=None):
        """Add an action to this process."""

        if not action_key:
            action_key = utils.generate_key()
        if not incoming:
            incoming = []
        if not outgoing:
            outgoing = []
        if is_complete and outgoing:
            is_complete = False
        action = Action.get_by_key_name(action_key, parent=self)
        if not action:
            action = Action(key_name=action_key, parent=self, process=self,
                            name=name)
        action.is_complete = bool(is_complete)

        for step_key in incoming:
            step = Step.get(step_key)
            if step:
                action.add_incoming_step(step, save=False)
        for step_key in outgoing:
            step = Step.get(step_key)
            if step:
                action.add_outgoing_step(step, save=False)

        action.put()
        return action

    def delete_stats(self):
        """Delete any statistic objects for this Process."""
        for stats in self.stats:
            stats.delete()

    @classmethod
    def from_dict(cls, client, data):
        """Return a new Process instance from a dict object."""

        if not (client and isinstance(client, Client)):
            raise exceptions.MissingException('No client found')

        if not (data and isinstance(data, dict)):
            raise exceptions.MissingException('No data found')

        kind = data.get('kind', None)
        name = data.get('name', None)

        if not name:
            raise exceptions.MissingException('Missing "name" parameter.')
        if not kind:
            raise exceptions.MissingException('Missing "kind" parameter.')
        if kind != cls.__name__:
            raise exceptions.MissingException('Expected "kind=%s", found ' \
                '"kind=%s".' % (cls.__name__, kind))

        process_key = data.get('key', None)
        if not process_key:
            process_key = utils.generate_key()
        description = data.get('description', None)
        collect_stats = data.get('collect_stats', None)

        process = cls.get_or_insert(process_key, client=client, name=name)
        process.description = description
        if collect_stats is not None:
            process.collect_stats = bool(collect_stats)
        return process

    def delete_steps_actions(self):
        """Delete this process' steps and actions."""

        entities = []
        entity_keys = []

        for action in self.actions:
            entities.append(action)
            entity_keys.append(action.id)

        for step in self.steps:
            entities.append(step)
            entity_keys.append(step.id)

        if entities:
            try:
                db.delete(entities)
            except apiproxy_errors.CapabilityDisabledError:
                raise exceptions.MaintenanceException('Unable to delete ' \
                    'steps and actions from Process "%s" due to ' \
                    'maintenance.' % self.id)
        if entity_keys:
            from google.appengine.api import memcache
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
        return step.is_valid()

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
    process = db.ReferenceProperty(Process, collection_name='steps',
                                   required=True)
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    is_start = db.BooleanProperty(default=False)
    team = db.ReferenceProperty(Team, collection_name='steps')
    members = db.ListProperty(basestring)

    @property
    def actions(self):
        """Return the actions that come after this step."""
        return Action.all().filter('incoming', self.key())

    @property
    def prior(self):
        """Return the actions that come before this step."""
        return Action.all().filter('outgoing', self.key())

    @property
    def last_updated(self):
        """Get the most recent non-actioned execution as the time this
        step was updated."""
        query = Execution.all()
        query.filter('step =', self)
        query.filter('action =', None)
        query.order('-start_date')

        execution = query.get()
        if not execution:
            return None
        return execution.start_date

    def is_valid(self):
        """A step is valid if it has at least one direct member or a team with
        members defined."""
        if self.members:
            return True
        elif self.team and self.team.members:
            return True
        return False

    def get_absolute_url(self):
        url = '%s/steps/%s.atom' % (settings.HTTPS_URL, self.id)
        return url

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

    def queue_tasks(self, request):
        """Queue execution tasks for a given request."""

        if not isinstance(request, Request):
            raise exceptions.InternalException('"%s" is not a valid Request ' \
                                               'model.' % request)
        if not self.is_valid():
            raise exceptions.InternalException('Step is not valid: no team ' \
                                               'or members found.')

        params = {'step_key': self.id, 'request_key': request.id}
        tasks = []
        queued_members = []
        if self.team:
            params['team_key'] = self.team.id
            for member in self.team.members:
                params['member'] = member

                task = taskqueue.Task(params=params)
                tasks.append(task)
                queued_members.append(member)
        params['team_key'] = None
        if self.members:
            for member in self.members:
                # Skip member if an execution has already been queued
                if member in queued_members:
                    continue
                params['member'] = member

                task = taskqueue.Task(params=params)
                tasks.append(task)
                queued_members.append(member)
        if tasks:
            queue = taskqueue.Queue('execution-creation')
            queue.add(tasks)

        # Queue up step PubSubHubbub hub notifications
        tasks = []
        for hub in Hub.all():
            task = taskqueue.Task(params={'step_key': self.id,
                'callback_url': hub.url})
            tasks.append(task)
        if tasks:
            queue = taskqueue.Queue('step-callback')
            queue.add(tasks)
        return True

    def get_executions(self, limit=100):
        """Return non-actioned executions with uncompleted requests in
        this step in creation order."""

        query = Execution.all()
        query.filter('step =', self)
        query.filter('action =', None)
        query.order('start_date')

        for execution in query.fetch(limit):
            if not execution.request.is_completed:
                yield execution


class Action(FlomosaBase):
    process = db.ReferenceProperty(Process, collection_name='actions',
                                   required=True)
    name = db.StringProperty(required=True)
    incoming = db.ListProperty(db.Key)
    outgoing = db.ListProperty(db.Key)
    is_complete = db.BooleanProperty(default=False)

    def put(self):
        if self.outgoing:
            self.is_complete = False
        else:
            self.is_complete = True
        super(Action, self).put()

    def add_incoming_step(self, step, save=True):
        """Add an incoming Step to this Action."""
        if step.key() not in self.incoming:
            self.incoming.append(step.key())
            if save:
                self.put()

    def add_outgoing_step(self, step, save=True):
        """Add an outgoing Step to this Action."""
        if step.key() not in self.outgoing:
            self.outgoing.append(step.key())
            if save:
                self.put()

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
            if step and step.id not in data['incoming']:
                data['incoming'].append(step.id)
        for step_key in self.outgoing:
            step = Step.get(step_key)
            if step and step.id not in data['outgoing']:
                data['outgoing'].append(step.id)
        return data


class Request(db.Expando):
    client = db.ReferenceProperty(Client, collection_name='requests',
                                  required=True)
    process = db.ReferenceProperty(Process, collection_name='requests',
                                   required=True)
    requestor = db.EmailProperty(required=True)
    contact = db.EmailProperty()
    is_draft = db.BooleanProperty(default=False)
    submitted_date = db.DateTimeProperty(auto_now_add=True)
    is_completed = db.BooleanProperty(default=False)
    completed_date = db.DateTimeProperty()
    duration = db.IntegerProperty(default=0) # seconds

    @property
    def id(self):
        """Return the unique ID for this request."""
        return self.key().id_or_name()

    def get_absolute_url(self):
        url = '%s/requests/%s.json' % (settings.HTTPS_URL, self.id)
        return url

    @classmethod
    def get(cls, key, client=None):
        """Lookup the request key in memcache and then the datastore."""
        request = cache.get_from_cache(cls, key)
        if client and client.id != request.client.id:
            raise exceptions.UnauthorizedException('Client "%s" is not ' \
                'authorized to access Request "%s".' % (client.id, request.id))
        return request

    def put(self):
        """Save the Request to the datastore and memcache and start the process
        after the first save."""

        start_process = False
        if not self.is_saved():
            start_process = True

        cache.save_to_cache(self)

        if start_process:
            # Lookup the start step in the process and create the first batch
            # of Execution objects to work on the request
            step = self.process.get_start_step()
            if not step:
                raise ValidationException('Process "%s" does not have a ' \
                                          'starting step.' % process.id)

            step.queue_tasks(self)

            import time
            # Record the request in the Process statistics
            task = taskqueue.Task(params={'request_key': self.id,
                'process_key': self.process.id, 'timestamp': time.time()})
            queue = taskqueue.Queue('request-statistics')
            queue.add(task)

        return self.key()

    def delete(self):
        """Delete the Request from the datastore and memcache."""
        return cache.delete_from_cache(self)

    def set_completed(self, completed_date=None):
        """Set the request has being completed."""

        if self.is_completed:
            return None

        # If we haven't already marked this request as being completed, set
        # the is_completed flag and compute the duration the request was in
        # progress, in seconds.

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
        """Return executions in creation order."""

        query = Execution.all()
        query.filter('request =', self)
        query.order('start_date')

        return query.fetch(100)

    def to_dict(self):
        """Return request as a dict object."""

        data = {
            'kind': self.kind(),
            'process': self.process.id,
            'requestor': self.requestor,
            'contact': self.contact,
            'is_draft': self.is_draft,
            'submitted_date': str(self.submitted_date),
            'is_completed': self.is_completed,
            'completed_date': str(self.completed_date),
            'duration': self.duration,
            'executions': []
        }
        for property in self.dynamic_properties():
            data[property] = getattr(self, property)
        for execution in self.get_executions():
            data['executions'].append(execution.to_dict())

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
    reminder_count = db.IntegerProperty(default=0)
    last_reminder_sent_date = db.DateTimeProperty()
    sent_date = db.DateTimeProperty()
    viewed_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    email_delay = db.IntegerProperty(default=0) # viewed_date-sent_date
    action_delay = db.IntegerProperty(default=0) # end_date-viewed_date
    duration = db.IntegerProperty(default=0) # end_date-start_date

    def get_absolute_url(self):
        url = '%s/executions/%s.json' % (settings.HTTPS_URL, self.id)
        return url

    def to_dict(self):
        """Return execution as a dict object."""

        data = {
            'kind': self.kind(),
            'process': self.process.id,
            'request': self.request.id,
            'step': self.step.id,
            'action': None,
            'team': None,
            'member': self.member,
            'start_date': str(self.start_date),
            'reminder_count': self.reminder_count,
            'last_reminder_sent_date': None,
            'sent_date': None,
            'viewed_date': None,
            'end_date': None,
            'email_delay': self.email_delay,
            'action_delay': self.action_delay,
            'duration': self.duration
        }
        actions = []
        for action in self.step.actions:
            action_data = {'kind': action.kind(), 'key': action.id,
                           'name': action.name,
                           'is_complete': action.is_complete}
            actions.append(action_data)
        data['available_actions'] = actions
        if self.last_reminder_sent_date:
            data['last_reminder_sent_date'] = str(self.last_reminder_sent_date)
        if self.sent_date:
            data['sent_date'] = str(self.sent_date)
        if self.viewed_date:
            data['viewed_date'] = str(self.viewed_date)
        if self.end_date:
            data['end_date'] = str(self.end_date)
        if self.action:
            data['action'] = self.action.id
        if self.team:
            data['team'] = self.team.id
        if self.is_saved():
            data['key'] = self.id
        return data

    def set_sent(self, sent_date=None):
        """Set this execution as being sent."""

        # Only set the sent timestamp once
        if self.sent_date:
            return None

        if not sent_date:
            sent_date = datetime.datetime.now()
        self.sent_date = sent_date

        return self.put()

    def set_completed(self, action, end_date=None):
        """Set this execution as being completed."""

        # Only set the action once
        if self.action or self.end_date:
            return None

        if not isinstance(action, Action):
            raise exceptions.InternalException('"%s" is not a valid Action ' \
                                               'model.' % action)

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

    def set_viewed(self, viewed_date=None):
        """Set this execution as being viewed."""

        # Only set the viewed timestamp once
        if self.viewed_date:
            return None

        if not viewed_date:
            viewed_date = datetime.datetime.now()
        self.viewed_date = viewed_date
        if self.sent_date and not self.email_delay:
            delta = self.viewed_date - self.sent_date
            self.email_delay = delta.days * 86400 + delta.seconds

        return self.put()

    def is_step_completed(self, limit=30):
        """Has this request step been completed by anyone?"""

        query = self.all()
        query.filter('step =', self.step)
        query.filter('request =', self.request)
        query.filter('member !=', self.member)
        query.order('member')
        query.order('-end_date')

        for execution in query.fetch(limit):
            if execution.action:
                return execution
        return False

    def num_passes(self, limit=5):
        """Return number of times through this step for this request."""

        query = self.all()
        query.filter('step =', self.step)
        query.filter('request =', self.request)
        query.filter('member =', self.member)
        return query.count(limit)


class Statistic(db.Model):
    process = db.ReferenceProperty(Process, collection_name='stats',
                                   required=True)
    type = db.StringProperty(required=True)
    year = db.IntegerProperty(required=True)
    month = db.IntegerProperty()
    day = db.IntegerProperty()
    hour = db.IntegerProperty()
    week_day = db.IntegerProperty() # ISO format 1 = Monday, 7 = Sunday
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
        """Store request data in a Statistic object."""

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
    def store_stat(cls, request, process, timestamp, type='daily', parent=None,
                   date_key=None):
        """Store a Statistic object"""

        if not isinstance(process, Process):
            raise exceptions.InternalException('"%s" is not a Process ' \
                                               'model.' % process)
        if not isinstance(request, Request):
            raise exceptions.InternalException('"%s" is not a Request ' \
                                               'model.' % request)

        valid_types = ('daily', 'hourly', 'weekly', 'monthly', 'yearly')
        if type not in valid_types:
            raise exceptions.InternalException('"%s" is an invalid type.' % \
                                               type)

        if not isinstance(timestamp, datetime.datetime):
            raise exceptions.InternalException('Timestamp is not a valid ' \
                                               'datetime object.')

        month = None
        day = None
        week_num = None
        week_day = None
        hour = None
        if date_key is None:
            if type == 'daily':
                date_key = '%d%02d%02d' % (timestamp.year, timestamp.month,
                                           timestamp.day)
                month = timestamp.month
                day = timestamp.day
                temp, week_num, week_day = timestamp.isocalendar()
            elif type == 'weekly':
                temp, week_num, week_day = timestamp.isocalendar()
                date_key = '%dW%02d' % (timestamp.year, week_num)
            elif type == 'monthly':
                date_key = '%d%02d' % (timestamp.year, timestamp.month)
                month = timestamp.month
            elif type == 'yearly':
                date_key = timestamp.year
            elif type == 'hourly':
                date_key = '%d%02d%02d%02d' % (timestamp.year, timestamp.month,
                                               timestamp.day, timestamp.hour)
                month = timestamp.month
                day = timestamp.day
                hour = timestamp.hour
                temp, week_num, week_day = timestamp.isocalendar()
            date_key = str(date_key)

        stat_key = '%s_%s' % (process.id, date_key)

        stat = cls.get_by_key_name(stat_key, parent=parent)
        if not stat:
            stat = cls(key_name=stat_key, parent=parent, process=process,
                       type=type, year=timestamp.year)
            stat.month = month
            stat.day = day
            stat.week_day = week_day
            stat.week_num = week_num
            stat.hour = hour
        stat.log(request)
        stat.put()
        return stat

    @classmethod
    def store_stats(cls, request, process, timestamp=None):
        """Store hourly, daily, weekly, monthly and yearly statstics."""

        if timestamp is None:
            timestamp = datetime.datetime.now()
        yearly = cls.store_stat(request, process, timestamp, type='yearly',
                                parent=process)
        monthly = cls.store_stat(request, process, timestamp, type='monthly',
                                 parent=yearly)
        weekly = cls.store_stat(request, process, timestamp, type='weekly',
                                parent=yearly)
        daily = cls.store_stat(request, process, timestamp, type='daily',
                               parent=weekly)
        hourly = cls.store_stat(request, process, timestamp, type='hourly',
                                parent=daily)

    def to_dict(self):
        """Return statistics as a dict object."""

        data = {
            'kind': self.kind(),
            'process': self.process.id,
            'type': self.type,
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'hour': self.hour,
            'week_day': self.week_day,
            'week_num': self.week_num,
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
