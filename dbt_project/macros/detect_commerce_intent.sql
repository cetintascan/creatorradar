{#
    Returns BOOLEAN. True if col contains Turkish commerce intent signals.
    Input: col — a lowercased SQL text expression (e.g. lower(video_title || ' ' || description))
    Output: BOOLEAN
#}
{% macro detect_commerce_intent(col) %}
(
    {{ col }} like '%nereden aldım%'
    or {{ col }} like '%fiyatı%'
    or {{ col }} like '%link%'
    or {{ col }} like '%indirim%'
    or {{ col }} like '%alınır mı%'
    or {{ col }} like '%muadil%'
    or {{ col }} like '%gratis%'
    or {{ col }} like '%watsons%'
    or {{ col }} like '%trendyol%'
    or {{ col }} like '%sephora%'
)
{% endmacro %}
