{% extends "base_email_text.tpl" %}

{% block msg %}
Your request has completed the "{{ process_name }}" process with an outcome
of "{{ action_name }}". Feel free to proceed with any follow-up activities
which may have pending.
{% endblock msg %}