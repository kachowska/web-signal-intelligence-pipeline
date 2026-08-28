-- Companies observed with Python in their latest state
SELECT DISTINCT c.domain
FROM companies c
JOIN observations o ON o.company_id = c.id
JOIN technology_signals t ON t.observation_id = o.id
WHERE t.technology = 'python'
ORDER BY c.domain;

-- Recent change events
SELECT c.domain, e.event_type, e.value, e.observed_at
FROM change_events e
JOIN companies c ON c.id = e.company_id
ORDER BY e.observed_at DESC
LIMIT 100;
