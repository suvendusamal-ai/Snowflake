{% snapshot customers_snapshot %}

{{
    config(
        target_schema='training_snapshots',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=true
    )
}}

select
    customer_id,
    customer_name,
    customer_segment,
    customer_status,
    created_at,
    updated_at
from {{ ref('stg_customers') }}

{% endsnapshot %}
