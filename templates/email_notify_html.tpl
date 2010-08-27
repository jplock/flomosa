{% extends "base_email_html.tpl" %}

{% block msg %}
<p>--- Reply ABOVE THIS LINE to take action on this request, or to post a comment ---</p>

<p>The following request has been sent to you for your action in the
<strong>{{ step_name }}</strong> step. Please reply to this email with one of
these phrases to move this request to the next step in the process. The phrase
needs to exactly match as written.</p>

<ul>
{% for action in actions %}
<li>"<a href="{{ url }}/viewed/{{ execution_key }}/{{ action.id }}.json">{{ action.name }}</a>"</li>
{% endfor %}
</ul>
{% endblock msg %}

{% block sig %}
<p>Thanks.</p>

<p>-Flomosa Team<img src="{{ url }}/viewed/{{ execution_key }}.json" height="1" width="1" border="0"/></p>
{% endblock sig %}