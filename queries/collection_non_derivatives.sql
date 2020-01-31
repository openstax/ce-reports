--for cnx/#838 - query for non-derived, non-openstax collections
select
	collections.*,
	persons.*
from (
	select
		m.moduleid as collection_id,
		m.name as collection_title,
		m.created as created_at,
		m.revised as last_revised,
		m.authors as authors,
		unnest(m.authors) as author
	from modules as m
	where m.parent is null
	and m.portal_type = 'Collection'
	and not 'OpenStaxCollege' = any(m.authors)) collections
left join (
	select
		p.personid as personid,
		p.firstname as first_name,
		p.surname as last_name,
		p.email as email
	from persons as p
	where p.email is not null) persons on persons.personid = collections.author
