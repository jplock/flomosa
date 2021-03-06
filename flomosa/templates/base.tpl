<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>{% block title %}Flomosa{% endblock %}</title>
</head>

<body id="flomosa">

    <div id="header">
        <div style="float:right">
            {% if current_client %}
                Welcome {{ current_client.email_address }},
                <a href="/">Home</a> -
                <a href="/account/">My Account</a> -
                <a href="/account/logout/">Logout</a>
            {% else %}
                <a href="/">Home</a> -
                <a href="/account/login/?next={{ uri|escape }} ">Login</a> -
                <a href="/account/register/?next={{ uri|escape }} ">Register</a>
            {% endif %}
        </div>
    </div>

    <div id="content">
        {% block content %}{% endblock %}
    </div>

    <div id="footer">
        <div class="copyright">&copy; 2010 Flomosa, LLC. All Rights Reserved.</div>
    </div>

    <script type="text/javascript">
    var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
    document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
    </script>
    <script type="text/javascript">
    try {
    var pageTracker = _gat._getTracker("UA-15357937-1");
    pageTracker._setDomainName(".flomosa.com");
    pageTracker._trackPageview();
    } catch(err) {}</script>

</body>
</html>