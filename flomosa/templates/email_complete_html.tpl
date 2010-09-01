{% extends "base_email_html.tpl" %}

{% block msg %}
<p>Your request has completed the <strong>{{ process_name }}</strong> process
with an outcome of <strong>{{ action_name }}</strong>. Feel free to proceed
with any follow-up activities which may have pending.</p>
{% endblock msg %}