<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<title>Flomosa</title>
</head>
<body>

<p>Your request has completed the <strong>{{ step_name }}</strong> step
in the <strong>{{ process_name }}</strong> process with an outcome of
<strong>{{ action_name }}</strong>. Please wait for any follow-up actions
until you receive the process completion email.</p>

<p>Below is the request data for your reference:</p>

<table border="1" cellpadding="2" cellspacing="0">
{% for key in request_data.items %}
<tr>
    <td align="right"><strong>{{ key.0 }}</strong></td>
    <td>{{ key.1 }}</td>
</tr>
{% endfor %}
</table>

<p>Thanks.</p>

<p>-Flomosa Team</p>

</body>
</html>