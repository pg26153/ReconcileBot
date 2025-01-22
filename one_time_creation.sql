-- Step 1: Create the reconciliation_failures table
CREATE TABLE reconciliation_failures (
    id INT PRIMARY KEY AUTO_INCREMENT,
    failure_message VARCHAR(255),
    failure_details TEXT,
    cycle_date DATE,
    status VARCHAR(50) DEFAULT 'unresolved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ticket VARCHAR(50)
);



-- Step 4: Retrieve the most recent unresolved failure record
SELECT *
FROM reconciliation_failures
WHERE cycle_date = CURRENT_DATE;



-- Extra steps
CREATE TABLE `sub_actor` (
  `actor_id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `first_name` varchar(45) NOT NULL,
  `last_name` varchar(45) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`actor_id`)
)

-- resolution query

INSERT INTO `sub_actor`
(`first_name`,
`last_name`,
`last_update`)
select 
first_name,
last_name,
last_update
From actor