select count(*) as actual_row_count
from {{ ref('fct_recognized_revenue') }}
having count(*) <> 6
