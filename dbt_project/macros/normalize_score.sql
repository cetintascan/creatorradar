{#
    Min-max normalization within a window partition.
    Input: col          — numeric SQL column expression
           partition_col — partition expression (use literal 1 for global normalization)
    Output: FLOAT64 in [0.0, 1.0]; NULL when all values in the partition are equal
#}
{% macro normalize_score(col, partition_col) %}
safe_divide(
    {{ col }} - min({{ col }}) over (partition by {{ partition_col }}),
    max({{ col }}) over (partition by {{ partition_col }}) - min({{ col }}) over (partition by {{ partition_col }})
)
{% endmacro %}
