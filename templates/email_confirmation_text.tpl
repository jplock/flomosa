Your replied action of "{{ action_name }}" in the "{{ step_name }}" has been confirmed.

Below is the request data for your reference:

* Key: {{ request_key }}
* Requestor: {{ requestor }}
* Submitted Date: {{ submitted_date }}

{% for key in request_data.items %}
* {{ key.0 }}: {{ key.1 }}
{% endfor %}

Thanks.

-Flomosa Team