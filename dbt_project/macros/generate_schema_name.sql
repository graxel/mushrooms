{%- macro generate_schema_name(custom_schema_name, node) -%}
  {%- if target.name in ['qa', 'prod', 'cloud'] -%}
    {{ custom_schema_name }}
  {%- else -%}
    {{ target.schema }}_{{ custom_schema_name }}
  {%- endif -%}
{%- endmacro -%}
