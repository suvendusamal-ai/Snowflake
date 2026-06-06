with source_data as (
    select *
    from {{ source('raw', 'customers') }}
),
standardized as (
    select
        customer_id,
        trim(customer_name) as customer_name,
        lower(trim(email)) as email,
        case
            when upper(trim(segment)) = 'SMB' then 'SMB' 
            else initcap(trim(segment))
        end as customer_segment,
        upper(trim(status)) as customer_status,
        created_at,
        updated_at,
        ingested_at
    from source_data
)
select *
from standardized