select count(*) as actual_row_count
from {{ ref('fct_sales_bookings') }}
having count(*) <> 8
