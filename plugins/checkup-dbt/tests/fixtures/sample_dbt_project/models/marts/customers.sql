-- Customer mart model with aggregated order data
select
    c.customer_id,
    c.customer_name,
    c.email,
    count(o.order_id) as total_orders,
    sum(o.amount) as total_amount
from {{ ref('stg_customers') }} as c
left join {{ ref('stg_orders') }} as o on c.customer_id = o.customer_id
group by c.customer_id, c.customer_name, c.email
