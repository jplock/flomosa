#!/usr/bin/env python

import uuid
import time
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import models

def purge_test_data(self):
    q = db.GqlQuery("SELECT __key__ FROM Process")
    results = q.fetch(10)
    db.delete(results)

    q = db.GqlQuery("SELECT __key__ FROM Step")
    results = q.fetch(10)
    db.delete(results)

    q = db.GqlQuery("SELECT __key__ FROM Team")
    results = q.fetch(10)
    db.delete(results)

    q = db.GqlQuery("SELECT __key__ FROM Action")
    results = q.fetch(10)
    db.delete(results)

    q = db.GqlQuery("SELECT __key__ FROM Request")
    results = q.fetch(10)
    db.delete(results)

def create_test_data(self):
    id = str(uuid.uuid4())
    p = models.Process(key_name=id, name='Test Process')
    p.put()

    id = str(uuid.uuid4())
    t = models.Team(key_name=id, name='Flomosa Testing Team')
    t.members = ['jplock@gmail.com']
    t.put()

    team_key = t.key()

    id = str(uuid.uuid4())
    s1 = models.Step(key_name=id, name='Step 1', process=p)
    s1.teams = [team_key]
    s1.is_start = True
    s1.put()
    s1_key = s1.key()

    id = str(uuid.uuid4())
    s2 = models.Step(key_name=id, name='Step 2', process=p)
    s2.teams = [team_key]
    s2.put()
    s2_key = s2.key()

    id = str(uuid.uuid4())
    s3 = models.Step(key_name=id, name='Step 3', process=p)
    s3.teams = [team_key]
    s3.put()
    s3_key = s3.key()

    a1 = models.Action(key_name=id, name='Step 1 - Approve', process=p)
    a1.incoming = [s1_key]
    a1.outgoing = [s2_key]
    a1.put()

    id = str(uuid.uuid4())
    a2 = models.Action(key_name=id, name='Step 1 - Decline', process=p)
    a2.incoming = [s1_key]
    a2.outgoing = [s1_key]
    a2.put()

    id = str(uuid.uuid4())
    a3 = models.Action(key_name=id, name='Step 2 - Approve', process=p)
    a3.incoming = [s2_key]
    a3.outgoing = [s3_key]
    a3.put()

    id = str(uuid.uuid4())
    a4 = models.Action(key_name=id, name='Step 2 - Decline', process=p)
    a4.incoming = [s2_key]
    a4.outgoing = [s1_key]
    a4.put()

    id = str(uuid.uuid4())
    a5 = models.Action(key_name=id, name='Step 3 - Approve', process=p)
    a5.incoming = [s3_key]
    a5.is_complete = True
    a5.put()

    id = str(uuid.uuid4())
    a6 = models.Action(key_name=id, name='Step 3 - Decline', process=p)
    a6.incoming = [s3_key]
    a6.outgoing = [s1_key]
    a6.put()

    id = str(uuid.uuid4())
    r1 = models.Request(key_name=id, requestor='jplock@gmail.com', process=p)
    r1.first_name = 'Justin'
    r1.last_name = 'Plock'
    r1.email = 'jplock@gmail.com'
    r1.text = 'asdf'
    r1.put()

    id = str(uuid.uuid4())
    r2 = models.Request(key_name=id, requestor='jplock@gmail.com', process=p)
    r2.first_name = 'Justin'
    r2.last_name = 'Plock'
    r2.email = 'jplock@gmail.com'
    r2.imp_date = time.time()
    r2.put()

    self.response.out.write(p.to_dot())

class MainHandler(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('Purging old test data<br/>')
        purge_test_data(self)
        #self.response.out.write('Creating new test data<br/>')
        create_test_data(self)
        #self.response.out.write('Done!<br/>')

def main():
    application = webapp.WSGIApplication([('/test', MainHandler)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()