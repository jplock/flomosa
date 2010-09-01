{% extends "base_email_html.tpl" %}

{% block msg %}
<p>Your replied action of <strong>{{ action_name }}</strong> in the
<strong>{{ step_name }}</strong> has been confirmed.</p>
{% endblock msg %}