{% extends "base_email_text.tpl" %}

{% block msg %}
Your request has completed the "{{ step_name }}" step in the "{{ process_name }}"
process with an outcome of "{{ action_name }}". Please wait for any
follow-up actions until you receive the process completion email.
{% endblock msg %}