{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='order_item_key',
        on_schema_change='sync_all_columns'
    )
}}

select
    order_item_key,
    order_id,
    line_number,
    order_date,
    order_status,
    customer_id,
    customer_name,
    customer_segment,
    product_name,
    quantity,
    unit_price,
    line_revenue,
    source_updated_at,
    current_timestamp() as dbt_loaded_at
from {{ ref('int_order_items_enriched') }}
where order_status = 'COMPLETED'

{% if is_incremental() %}
  and source_updated_at >= (
      select coalesce(dateadd(day, -1, max(source_updated_at)), '1900-01-01'::timestamp_ntz)
      from {{ this }}
  )
{% endif %}
