select *
from {{ ref('geocode_consolidated') }}
where geometry__location__lat is null
   or geometry__location__lng is null
   or geometry__location__lat < -90
   or geometry__location__lat > 90
   or geometry__location__lng < -180
   or geometry__location__lng > 180
