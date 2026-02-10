select *
from {{ ref('geocode_consolidated') }}
where formatted_address is null
