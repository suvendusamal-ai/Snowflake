select
    product_id,
    product_name,
    product_category,
    unit_price as current_unit_price,
    active_flag,
    updated_at
from {{ ref('stg_products') }}