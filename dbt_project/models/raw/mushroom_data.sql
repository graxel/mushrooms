WITH raw AS (
    SELECT ROW_NUMBER() OVER (ORDER BY 1) AS mushroom_id, *
    FROM {{ ref('mushroom_csv') }}
),
final AS (
    SELECT *
    FROM raw
)
SELECT * FROM final LIMIT {{ var('data_size') }}
