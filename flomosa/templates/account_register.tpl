{% extends "base.tpl" %}

{% block title %}Flomosa - Register{% endblock title %}

{% block content %}

<h1>Register</h1>

{% if messages %}
    <div id="messages">
        <ul>
        {% for message in messages %}
        <li>{{ message }}</li>
        {% endfor %}
        </ul>
    </div>
{% endif %}

<form method="POST" action="/account/register/">
<input type="hidden" name="next" value="{{ next }}"/>
<div>
    <label for="email_address">Email Address</label>
    <input type="text" name="email_address" value="{{ email_address }}" size="30" maxlength="80"/>
</div>
<div>
    <label for="password">Password</label>
    <input type="text" name="password" size="30"/>
</div>
<div>
    <label for="confirm_password">Confirm Password</label>
    <input type="text" name="confirm_password" size="30"/>
</div>
<div>
    <label for="first_name">First Name</label>
    <input type="text" name="first_name" value="{{ first_name }}" size="30" maxlength="50"/>
</div>
<div>
    <label for="last_name">Last Name</label>
    <input type="text" name="last_name" value="{{ last_name }}" size="30" maxlength="50"/>
</div>
<div>
    <label for="first_name">Company</label>
    <input type="text" name="company" value="{{ company }}" size="30" maxlength="50"/>
</div>
<div>
    <input type="submit" value="Register"/> <a href="/">Cancel</a>
</div>
</form>

{% endblock content %}