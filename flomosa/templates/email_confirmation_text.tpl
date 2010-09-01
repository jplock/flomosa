{% extends "base_email_text.tpl" %}

{% block msg %}
Your replied action of "{{ action_name }}" in the "{{ step_name }}" has been confirmed.
{% endblock msg %}