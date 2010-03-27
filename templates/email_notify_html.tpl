<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<title>Flomosa</title>
</head>
<body>

<p>--- Reply ABOVE THIS LINE to take action on this request, or to post a comment ---</p>

<p>The following request has been sent to you for your action in the
<strong>{{ step_name }}</strong> step. Please reply to this email with one of
these phrases to move this request to the next step in the process. The phrase
needs to exactly match as written.</p>

<ul>
{% for action in actions %}
<li>"<a href="http://flomosa.appspot.com/viewed/{{ execution_key }}/{{ action.id }}.json">{{ action.name }}</a>"</li>
{% endfor %}
</ul>

<p>Below is the request data:</p>

<table border="0" cellpadding="2" cellspacing="0">
<tr>
    <td align="right"><strong>Key</strong></td>
    <td>{{ request_key }}</td>
</tr>
<tr>
    <td align="right"><strong>Requestor</strong></td>
    <td><a href="mailto:{{ requestor }}">{{ requestor }}</a></td>
</tr>
<tr>
    <td align="right"><strong>Submitted Date</strong></td>
    <td>{{ submitted_date }}</td>
</tr>
</table>

<table border="1" cellpadding="2" cellspacing="0">
<tr>
    <th><strong>Name</strong></th>
    <th><strong>Value</strong></th>
</tr>
{% for key in request_data.items %}
<tr>
    <td align="right"><strong>{{ key.0 }}</strong></td>
    <td>{{ key.1 }}</td>
</tr>
{% endfor %}
</table>

<p>Thanks.</p>

<p>-Flomosa Team<img src="http://flomosa.appspot.com/viewed/{{ execution_key }}.json" height="1" width="1" border="0"/></p>

</body>
</html>