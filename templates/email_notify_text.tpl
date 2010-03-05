The following request has been sent to you for approval. Please reply
to this email with one of these phrases to move this request along:

{% for action in actions %}
- "{{ action.name }}"
{% endfor %}

Below is the request data:

{% for value in request_data.items %}
{{ key }} = {{ value }}
{% endfor %}

Thanks.

-Flomosa Team