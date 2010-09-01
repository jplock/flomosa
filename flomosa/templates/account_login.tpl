{% extends "base.tpl" %}

{% block title %}Flomosa - Login{% endblock title %}

{% block content %}

<h1>Login</h1>

{% if messages %}
    <div id="messages">
        <ul>
        {% for message in messages %}
        <li>{{ message }}</li>
        {% endfor %}
        </ul>
    </div>
{% endif %}

<form method="POST" action="/account/login/">
<input type="hidden" name="next" value="{{ next }}"/>
<div>
    <label for="email_address">Email Address</label>
    <input type="text" name="email_address" value="{{ email_address }}" size="30" maxlength="80"/>
</div>
<div>
    <label for="password">Password</label>
    <input type="password" name="password" size="30"/>
</div>
<div>
    <input type="submit" value="Login"/> <a href="/">Cancel</a>
</div>
</form>

{% endblock content %}