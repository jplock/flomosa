Your request has completed the "{{ process_name }}" process with an outcome
of "{{ action_name }}". Feel free to proceed with any follow-up activities
which may have pending.

Below is the request data for your reference:

{% for key in request_data.items %}
* {{ key.0 }}: {{ key.1 }}
{% endfor %}

Thanks.

-Flomosa Team