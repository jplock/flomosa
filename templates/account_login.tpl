{% extends "base.tpl" %}

{% block title %}Flomosa - Login{% endblock title %}

{% block content %}

<h1>Login</h1>

<form method="POST" action="/account/login/">
<div>
    <label for="email_address">Email Address</label>
    <input type="text" name="email_address" size="30" maxlength="80"/>
</div>
<div>
    <label for="password">Password</label>
    <input type="password" name="password" size="30"/>
</div>
<div>
    <input type="submit" name="Login"/>
</div>
</form>

{% endblock content %}