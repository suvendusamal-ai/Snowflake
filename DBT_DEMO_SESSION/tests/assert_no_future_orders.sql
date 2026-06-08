select *
from {{ ref('stg_orders') }}
where order_date > current_date()
