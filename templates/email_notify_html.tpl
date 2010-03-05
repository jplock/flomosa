<p>The following request has been sent to you for approval. Please reply
to this email with one of these phrases to move this request along:</p>

<ul>
{% for action in actions %}
<li>"<a href="http://127.0.0.1:8080/do/{{ execution_key }}.json">{{ action.name }}</a>"</li>
{% endfor %}
</ul>

<p>Below is the request data:</p>

<ul>
{% for value in request_data.items %}
<li>{{ key }} = {{ value }}</li>
{% endfor %}
</ul>

<p>Thanks.</p>

<p>-Flomosa Team<img src="http://127.0.0.1:8080/viewed/{{ execution_key }}.json" height="1" width="1" border="0"/></p>