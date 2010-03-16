Your request has completed the "{{ step_name }}" step in the "{{ process_name }}"
process with an outcome of "{{ action_name }}". Please wait for any
follow-up actions until you receive the process completion email.

Below is the request data for your reference:

{% for key in request_data.items %}
* {{ key.0 }}: {{ key.1 }}
{% endfor %}

Thanks.

-Flomosa Team