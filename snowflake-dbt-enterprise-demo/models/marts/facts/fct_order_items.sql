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
    currency_code,
    customer_id,
    product_id,
    quantity,
    unit_price,
    discount_pct,
    gross_line_amount,
    net_line_amount,
    net_line_amount_usd,
    source_updated_at,
    current_timestamp() as dbt_loaded_at
from {{ ref('int_order_lines_enriched') }}

{% if is_incremental() %}

where source_updated_at >= (
    select coalesce(
        dateadd(day, -1, max(source_updated_at)),
        '1900-01-01'::timestamp_ntz
    )
    from {{ this }}
)

{% endif %}