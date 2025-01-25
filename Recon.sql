-- Validation 1: Source vs Target - Missing Actors in sub_actor Table
INSERT INTO reconciliation_failures (failure_message, failure_details, cycle_date)
SELECT
    'Mismatch in reconciliation - Source vs Target' AS failure_message,
    CONCAT(
        COUNT(*), ' Actor(s) missing in sub_actor table'
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
    'Mismatch in reconciliation - Data Validation between source and target' AS failure_message,
    CONCAT(
        COUNT(*), ' Actor(s) with mismatched details between actor and sub_actor tables'
    ) AS failure_details,
    CURRENT_DATE AS cycle_date
FROM
    actor s
JOIN
    sub_actor t ON s.actor_id = t.actor_id
WHERE
    (s.first_name != t.first_name OR s.last_name != t.last_name);


-- Step 3: Mark unresolved failures as resolved if no discrepancies are found

-- Step 1: Create a temporary table to sfind out the ticket which needs to be set as resolved.
CREATE TEMPORARY TABLE temp_failures AS
SELECT id,failure_message, failure_details
FROM reconciliation_failures f1
WHERE f1.cycle_date = CURRENT_DATE - INTERVAL 1 DAY
  AND NOT EXISTS (
      SELECT 1 
      FROM reconciliation_failures f2
      WHERE f2.cycle_date = CURRENT_DATE
      AND f1.failure_message = f2.failure_message
      AND f1.failure_details = f2.failure_details
  );

-- Step 2: Update the reconciliation_failures table
UPDATE reconciliation_failures tgt
JOIN temp_failures src
ON src.id=tgt.id
SET tgt.status = 'Resolved';


-- Step 3: Drop the temporary table after the update is complete
DROP TEMPORARY TABLE IF EXISTS temp_failures;
