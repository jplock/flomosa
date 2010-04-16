{% extends "base_email_html.tpl" %}

{% block msg %}
<p>Your request has completed the <strong>{{ step_name }}</strong> step
in the <strong>{{ process_name }}</strong> process with an outcome of
<strong>{{ action_name }}</strong>. Please wait for any follow-up actions
until you receive the process completion email.</p>
{% endblock msg %}