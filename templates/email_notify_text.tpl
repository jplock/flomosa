Your action of "{{ action_name }}" in the {}

The following request has been sent to you for your action in the
"{{ step_name }}" step. Please reply to this email with one of these phrases to
move this request to the next step in the process. The phrase needs to exactly
match as written.

{% for action in actions %}
* "{{ action.name }}"
{% endfor %}

Below is the request data:

* Key: {{ request_key }}
* Requestor: {{ requestor }}
* Submitted Date: {{ submitted_date }}

{% for key in request_data.items %}
* {{ key.0 }}: {{ key.1 }}
{% endfor %}

Thanks.

-Flomosa Team