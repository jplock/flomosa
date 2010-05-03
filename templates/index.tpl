{% extends "base.tpl" %}

{% block content %}

{% if current_client %}

<h1>Processes</h1>

<table border="1" cellpadding="0" cellspacing="2">
<tr>
    <th>ID</th>
    <th>Name</th>
    <th>Description</th>
    <th>&nbsp;</th>
</tr>
{% for process in current_client.processes %}
<tr>
    <td>{{ process.id }}</td>
    <td>{{ process.name }}</td>
    <td>{{ process.description }}</td>
    <td><a href="/processes/{{ process.id }}.json" onclick="return confirm('Are you sure you want to delete this process?')">delete</a></td>
</tr>
{% endfor %}
</table>

<h1>Teams</h1>

<table border="1" cellpadding="0" cellspacing="2">
<tr>
    <th>ID</th>
    <th>Name</th>
    <th>Description</th>
    <th>&nbsp;</th>
</tr>
{% for team in current_client.teams %}
<tr>
    <td>{{ team.id }}</td>
    <td>{{ team.name }}</td>
    <td>{{ team.description }}</td>
    <td><a href="/teams/{{ team.id }}.json" onclick="return confirm('Are you sure you want to delete this team?')">delete</a></td>
</tr>
{% endfor %}
</table>

{% else %}
Coming Soon!
{% endif %}

{% endblock content %}