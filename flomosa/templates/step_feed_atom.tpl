<?xml version="1.0" encoding="utf-8"?>
<atom:feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">{{ step.name }}</title>
    <link rel="self" href="{{ step.get_absolute_url }}" type="application/atom+xml" />
    {% for hub in hubs %}
    <link rel="hub" href="{{ hub.url }}" />
    {% endfor %}
    <generator uri="{{ url }}/">Flomosa</generator>
    <id>urn:uuid:{{ step.id }}</id>
    <updated>{{ step.last_updated|date:"Y-m-d\TH:i:s\Z" }}</updated>
    <author>
        <name>{{ step.process.name }}</name>
        <email>{{ email }}</email>
    </author>
    {% for execution in step.get_executions %}
    <entry>
        <title>{{ execution.request.id }}</title>
        <link rel="alternate" href="{{ execution.get_absolute_url }}" type="application/json" />
        <id>urn:uuid:{{ execution.id }}</id>
        <updated>{{ execution.start_date|date:"Y-m-d\TH:i:s\Z" }}</updated>
        <author>
            <name>{{ execution.request.requestor }}</name>
            <email>{{ execution.request.requestor }}</email>
        </author>
    </entry>
    {% endfor %}
</atom:feed>