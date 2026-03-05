{% macro get_categorical_columns(table_ref, exclude_columns=[]) %}
  {# Get all columns from the table #}
  {% set columns = adapter.get_columns_in_relation(table_ref) %}
  
  {# Filter to keep only string/varchar columns and exclude specified ones #}
  {% set categorical_cols = [] %}
  {% for col in columns %}
    {% if col.dtype | upper in ('TEXT', 'VARCHAR', 'STRING', 'CHAR') 
       and col.name not in exclude_columns %}
      {% do categorical_cols.append(col.name) %}
    {% endif %}
  {% endfor %}
  
  {{ return(categorical_cols) }}
{% endmacro %}