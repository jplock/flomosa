<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>{{ step.name }}</title>
    <link href="{{ url }}/steps/{{ step.id }}/atom.xml" rel="self" />
    <link href="{{ url }}/" />
    <generator>Flomosa</generator>
    <id>urn:uuid:{{ step.id }}</id>
    <updated>{{ step.last_updated|date:"c" }}Z</updated>
    <author>
        <name>{{ step.process.name }}</name>
        <email>{{ email }}</email>
    </author>
    {% for execution in step.get_executions %}
    <entry>
        <title>{{ execution.request.id }}</title>
        <link href="{{ url }}/executions/{{ execution.id }}.json" />
        <id>urn:uuid:{{ execution.id }}</id>
        <updated>{{ execution.start_date|date:"c" }}Z</updated>
        <author>
            <name>{{ execution.request.requestor }}</name>
            <email>{{ execution.request.requestor }}</email>
        </author>
        <content type="html">
            &lt;ul&gt;
            {% for action in actions %}
                &lt;li&gt;&lt;a href="{{ url }}/viewed/{{ execution.id }}/{{ action.id }}.json"&gt;{{ action.name }}&lt;/a&gt;&lt;/li&gt;
            {% endfor %}
            &lt;/ul&gt;
        </content>
    </entry>
    {% endfor %}
</feed>