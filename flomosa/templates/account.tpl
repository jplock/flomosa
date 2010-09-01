{% extends "base.tpl" %}

{% block title %}Flomosa - My Account{% endblock title %}

{% block content %}

<h1>My Account</h1>

{% if messages %}
    <div id="messages">
        <ul>
        {% for message in messages %}
        <li>{{ message }}</li>
        {% endfor %}
        </ul>
    </div>
{% endif %}

<form method="POST" action="/account/">
<div>
    <label for="email_address">Email Address</label>
    {{ email_address }}
</div>
<div>
    <label for="old_password">Old Password</label>
    <input type="text" name="old_password" size="30"/>
</div>
<div>
    <label for="new_password">New Password</label>
    <input type="text" name="new_password" size="30"/>
</div>
<div>
    <label for="confirm_password">Confirm New Password</label>
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
    <label for="oauth_token">OAuth Key</label>
    {{ client_key }}
</div>
<div>
    <label for="oauth_secret">OAuth Secret</label>
    {{ oauth_secret }}
</div>
<div>
    <input type="submit" value="Save Changes"/> <a href="/account/">Cancel</a>
</div>
</form>

<h4><a href="/account/close/">Close My Account</a></h4>

{% endblock content %}