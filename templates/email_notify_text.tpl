{% extends "base_email_text.tpl" %}

{% block msg %}
--- Reply ABOVE THIS LINE to take action on this request, or to post a comment ---

The following request has been sent to you for your action in the
"{{ step_name }}" step. Please reply to this email with one of these phrases to
move this request to the next step in the process. The phrase needs to exactly
match as written.

{% for action in actions %}
* "{{ action.name }}"
{% endfor %}
{% endblock msg %}