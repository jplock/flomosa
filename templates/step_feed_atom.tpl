<?xml version="1.0" encoding="utf-8"?>
<atom:feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">{{ step.name }}</title>
    <link rel="self" href="{{ url }}/steps/{{ step.id }}.atom" type="application/atom+xml" />
    <link rel="alternate" href="{{ url }}/" type="text/html" hreflang="en"/>
    {% for hub in hubs %}
    <link rel="hub" href="{{ hub.url }}" />
    {% endfor %}
    <generator uri="{{ url }}/">Flomosa</generator>
    <id>urn:uuid:{{ step.id }}</id>
    <updated>{{ step.last_updated|date:"c" }}Z</updated>
    <author>
        <name>{{ step.process.name }}</name>
        <email>{{ email }}</email>
    </author>
    {% for execution in step.get_executions %}
    <entry>
        <title>{{ execution.request.id }}</title>
        <link rel="alternate" href="{{ url }}/executions/{{ execution.id }}.json" type="application/json" />
        <id>urn:uuid:{{ execution.id }}</id>
        <updated>{{ execution.start_date|date:"c" }}Z</updated>
        <author>
            <name>{{ execution.request.requestor }}</name>
            <email>{{ execution.request.requestor }}</email>
        </author>
    </entry>
    {% endfor %}
</atom:feed>