{#
    Returns BOOLEAN. True if col contains Turkish sponsor/partnership signals.
    Input: col — a lowercased SQL text expression (e.g. lower(video_title || ' ' || description))
    Output: BOOLEAN
#}
{% macro detect_sponsor_signal(col) %}
(
    {{ col }} like '%iş birliği%'
    or {{ col }} like '%işbirliği%'
    or {{ col }} like '%reklam%'
    or {{ col }} like '%sponsor%'
    or {{ col }} like '%affiliate%'
    or {{ col }} like '%indirim kodu%'
    or {{ col }} like '%kodum%'
    or {{ col }} like '%trendyol link%'
    or {{ col }} like '%gratis link%'
    or {{ col }} like '%watsons link%'
)
{% endmacro %}
