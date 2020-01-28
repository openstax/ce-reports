/* Query of Collection Derivatives of CNX for https://github.com/openstax/cnx/issues/642 */
/* Note: Left join to persons because some of the submitters are not in the persons table */

select
	m.name as canonical_title,
	m.moduleid as canonical_colid,
	m.portal_type as canonical_type,
	lm.name as derivative_title,
	lm.moduleid as derivative_colid,
	lm.portal_type as derivative_type,
    lm.created as created_at,
	lm.revised as last_revised,
	p.firstname as first_name,
	p.surname as last_name,
	p.email as email
from latest_modules as lm
join (
	select module_ident, name, moduleid, portal_type
	from modules
	where 'OpenStaxCollege' = any(authors)
	and portal_type='Collection') m on m.module_ident = lm.parent
left join persons as p on p.personid = lm.submitter
where lm.portal_type = 'Collection';
