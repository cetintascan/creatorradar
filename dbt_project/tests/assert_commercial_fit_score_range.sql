-- Returns rows where commercial_fit_score falls outside [0, 1]. Zero rows = test passes.
select channel_id, commercial_fit_score
from {{ ref('mart_creator_profiles') }}
where commercial_fit_score < 0 or commercial_fit_score > 1
