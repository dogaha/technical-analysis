-- macro for overriding dbt adding profile, schema name before assigned schema
-- must be exact
-- custom_schema_name piped into a trim of schema if it exists, else use default schema
{% macro generate_schema_name(custom_schema_name, node) %}
    {{ custom_schema_name | trim if custom_schema_name else schema }}
{% endmacro %}