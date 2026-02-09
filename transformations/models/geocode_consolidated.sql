{{
  config(
    materialized='table',
    schema='dwh',
    indexes=[
      {'columns': ['geocode_results_id'], 'unique': False},
      {'columns': ['formatted_address'], 'unique': False},
      {'columns': ['geometry__location__lat', 'geometry__location__lng'], 'unique': False}
    ]
  )
}}

with geocode_main as (
  select
    gr._dlt_id as geocode_results_id,
    gr.formatted_address,
    gr.geometry__location__lat,
    gr.geometry__location__lng,
    gr.geometry__location_type,
    gr.place_id,
    gr.partial_match
  from {{ source('staging', 'geocode_results') }} gr
),

address_components as (
  select
    grac._dlt_parent_id as geocode_results_id,
    string_agg(distinct grac.long_name, ', ') as address_components_text
  from {{ source('staging', 'geocode_results__address_components') }} grac
  group by grac._dlt_parent_id
),

location_types as (
  select
    grgt._dlt_parent_id as geocode_results_id,
    string_agg(distinct grgt.value, ', ') as location_types
  from {{ source('staging', 'geocode_results__types') }} grgt
  group by grgt._dlt_parent_id
),

navigation_points as (
  select
    grnp._dlt_parent_id as geocode_results_id,
    count(*) as navigation_points_count,
    string_agg(
      concat('lat:', round(grnp.location__latitude::numeric, 6), ' lng:', round(grnp.location__longitude::numeric, 6)),
      ' | '
    ) as navigation_points
  from {{ source('staging', 'geocode_results__navigation_points') }} grnp
  group by grnp._dlt_parent_id
)

select
  gm.geocode_results_id,
  gm.formatted_address,
  gm.geometry__location__lat,
  gm.geometry__location__lng,
  gm.geometry__location_type,
  gm.place_id,
  gm.partial_match,
  ac.address_components_text,
  lt.location_types,
  np.navigation_points_count,
  np.navigation_points
from geocode_main gm
left join address_components ac on gm.geocode_results_id = ac.geocode_results_id
left join location_types lt on gm.geocode_results_id = lt.geocode_results_id
left join navigation_points np on gm.geocode_results_id = np.geocode_results_id
