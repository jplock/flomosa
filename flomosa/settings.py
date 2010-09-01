#
# Copyright 2010 Flomosa, LLC
#

# Application name on AppEngine
APPLICATION_NAME = 'flomosa'

# Name of the secure cookie
COOKIE_NAME = APPLICATION_NAME

# Salt to use for encrypting the secure cookie
COOKIE_SECRET = 'F10m0sA'

# Email address to receive feedback at
FEEDBACK_EMAIL = 'feedback@flomosa.com'

# Full email domain name on AppEngine
EMAIL_DOMAIN = '%s.appspotmail.com' % APPLICATION_NAME

# Full URL domain name on AppEngine
URL_DOMAIN = '%s.appspot.com' % APPLICATION_NAME

# Full HTTP domain URL
HTTP_URL = 'http://%s' % URL_DOMAIN

# Full HTTPS domain URL
HTTPS_URL = 'https://%s' % URL_DOMAIN

# Email address on AppEngine to receive feedback at
FEEDBACK_FORWARDER_EMAIL = 'feedback@%s' % EMAIL_DOMAIN

# Maximum number of reminders to send
REMINDER_LIMIT = 10

# How often to send a reminder email (in seconds)
REMINDER_DELAY = 43200 # 12 hours

# Number of times to retry the datastore
DATASTORE_RETRY_ATTEMPTS = 5