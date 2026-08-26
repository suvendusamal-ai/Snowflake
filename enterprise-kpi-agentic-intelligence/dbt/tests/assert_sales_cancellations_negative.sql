with invalid_cancellations as (
    select event_id
    from {{ ref('stg_sales_order_events') }}
    where event_type = 'CANCELLATION' and amount >= 0
),
missing_fixture_cancellation as (
    select 'MISSING_CANCELLATION' as event_id
    where not exists (
        select 1
        from {{ ref('stg_sales_order_events') }}
        where event_type = 'CANCELLATION'
    )
)
select event_id from invalid_cancellations
union all
select event_id from missing_fixture_cancellation
