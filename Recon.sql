-- Validation 1: Source vs Target - Missing Actors in sub_actor Table
INSERT INTO reconciliation_failures (failure_message, failure_details, cycle_date)
SELECT
    'Mismatch in reconciliation - Source vs Target' AS failure_message,
    CONCAT(
        COUNT(*), ' actor(s) missing in sub_actor table'
    ) AS failure_details,
    CURRENT_DATE AS cycle_date
FROM
    actor s
LEFT JOIN
    sub_actor t ON s.actor_id = t.actor_id
WHERE
    t.actor_id IS NULL;

-- Validation 2: Data Validation - Mismatch in Actor Details Between actor and sub_actor
INSERT INTO reconciliation_failures (failure_message, failure_details, cycle_date)
SELECT
    'Mismatch in sql - Data Validation' AS failure_message,
    CONCAT(
        COUNT(*), ' actor(s) with mismatched details between actor and sub_actor tables'
    ) AS failure_details,
    CURRENT_DATE AS cycle_date
FROM
    actor s
JOIN
    sub_actor t ON s.actor_id = t.actor_id
WHERE
    (s.actor_name != t.actor_name OR s.actor_role != t.actor_role); -- Adjust column names based on actual schema


-- Step 3: Mark unresolved failures as resolved if no discrepancies are found

-- Step 1: Create a temporary table to store the previous cycle's failure messages and details
CREATE TEMPORARY TABLE temp_failures AS
SELECT failure_message, failure_details
FROM reconciliation_failures
WHERE cycle_date = (SELECT MAX(cycle_date) - 1 FROM reconciliation_failures);

-- Step 2: Update the reconciliation_failures table
UPDATE reconciliation_failures tgt
JOIN temp_failures src
ON src.failure_message = tgt.failure_message
AND src.failure_details = tgt.failure_details
SET tgt.status = 'resolved'
WHERE NOT EXISTS (
    SELECT 1 
    FROM reconciliation_failures rf
    WHERE rf.cycle_date = (SELECT MAX(cycle_date) FROM reconciliation_failures)
    AND rf.failure_message = src.failure_message
    AND rf.failure_details = src.failure_details
);

-- Step 3: Drop the temporary table after the update is complete
DROP TEMPORARY TABLE IF EXISTS temp_failures;

