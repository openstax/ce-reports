select
    lm.parent,
    lm.canonical,
	lm.moduleid as module_id,
	lm.name as title,
	lm.created as created_at,
	lm.revised as last_revised,
	lm.authors,
	lm.submitter,
	p.firstname as first_name,
	p.surname as last_name,
	p.email as email
from modules as lm
left join persons as p on p.personid = lm.submitter
where lm.portal_type = 'Module'
and parent is null
and canonical is null
and not('OpenStaxCollege' = any(authors));
