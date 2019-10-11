/* Query of Collection Derivatives of CNX for https://github.com/openstax/cnx/issues/642 */
/* Note: Left join to persons because some of the submitters are not in the persons table */

select
	lm.portal_type as module_type,
	m.moduleid as canonical_col_id,
	m.name as canonical_title,
	lm.moduleid as derivative_col_id,
	lm.name as derivative_title,
	lm.created as created_at,
	lm.revised as last_revised,
	p.firstname as first_name,
	p.surname as last_name,
	p.email as email
from latest_modules as lm
left join persons as p on p.personid = lm.submitter
inner join modules as m on m.module_ident = lm.parent
where lm.portal_type = 'Collection'
and 'OpenStaxCollege' != any(lm.authors)
and lm.parent in (
	select module_ident
	from modules
	where 'OpenStaxCollege' = any(authors)
	and portal_type = 'Collection');
