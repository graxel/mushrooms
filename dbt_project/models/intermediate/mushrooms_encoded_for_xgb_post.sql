{% set source_table = ref('mushroom_data_post') %}
{% set encoding_table = ref('categorical_encodings') %}
{% set categorical_columns = get_categorical_columns(source_table) %}

SELECT 
  t.mushroom_id,
  {% for column in categorical_columns %}
  enc_{{ column }}.encoded_value as {{ column }}_encoded
  {% if not loop.last %},{% endif %}
  {% endfor %}
FROM {{ source_table }} t
{% for column in categorical_columns %}
LEFT JOIN {{ encoding_table }} enc_{{ column }}
  ON enc_{{ column }}.column_name = '{{ column }}'
  AND enc_{{ column }}.original_value = t.{{ column }}
{% endfor %}
