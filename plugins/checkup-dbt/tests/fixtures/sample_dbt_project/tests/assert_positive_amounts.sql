-- Singular test to check that all amounts are positive
select *
from {{ ref('stg_orders') }}
where amount < 0
