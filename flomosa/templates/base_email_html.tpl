<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<title>Flomosa</title>
</head>
<body>

{% block msg %}{% endblock msg %}

<p>Below is the request data for your reference:</p>

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
{% for key in request_data.items %}
<tr>
    <td align="right"><strong>{{ key.0 }}</strong></td>
    <td>{{ key.1 }}</td>
</tr>
{% endfor %}
</table>

{% block sig %}
<p>Thanks.</p>

<p>-Flomosa Team</p>
{% endblock sig %}

</body>
</html>