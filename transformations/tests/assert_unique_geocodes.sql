select geocode_results_id, count(*)
from {{ ref('geocode_consolidated') }}
group by geocode_results_id
having count(*) > 1
