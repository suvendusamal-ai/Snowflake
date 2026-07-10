select
    product_id,
    trim(product_name) as product_name,
    initcap(trim(category)) as product_category,
    unit_price,
    active_flag,
    updated_at,
    ingested_at
from {{ source('raw', 'products') }}