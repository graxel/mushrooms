{# Reference bronze table #}
{% set source_table = ref('mushroom_data') %}

{# Get all categorical columns - exclude any we don't want encoded #}
{% set categorical_columns = get_categorical_columns(
    source_table
) %}

{# Build the UNION ALL query dynamically #}
WITH 
{% for column in categorical_columns %}
  {% if not loop.first %},{% endif %}
  {{ column }}_encoding AS (
    SELECT 
      '{{ column }}' as column_name,
      {{ column }} as original_value,
      COUNT(*) as value_count
    FROM {{ source_table }}
    WHERE {{ column }} IS NOT NULL
    GROUP BY {{ column }}
  )
{% endfor %}

, combined AS (
  {% for column in categorical_columns %}
    SELECT * FROM {{ column }}_encoding
    {% if not loop.last %}UNION ALL{% endif %}
  {% endfor %}
)

SELECT 
  column_name,
  original_value,
  DENSE_RANK() OVER (
    PARTITION BY column_name 
    ORDER BY original_value
  ) - 1 as encoded_value,
  value_count
FROM combined
ORDER BY column_name, encoded_value