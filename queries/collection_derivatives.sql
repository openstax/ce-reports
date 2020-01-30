/* Query of Collection Derivatives of CNX for https://github.com/openstax/cnx/issues/821 */
/* Note: Left join to persons because some of the submitters are not in the persons table */

select table2.*, table1.*
from 
	(select 
	 	m.parent as derivative_parent,
		m.module_ident as derivative_module_ident,
		m.name as derivative_title,
		m.moduleid as derivative_colid,
		m.portal_type as derivative_type,
	     	m.created as created_at, 
		m.revised as last_revised,
		m.submitter as submitter,
	    	p.firstname as first_name,
		p.surname as last_name,
		p.email as email
	from modules as m
	left join persons as p on p.personid = m.submitter
	where m.portal_type = 'Collection'
	and m.parent is not null) as table1
join 
	(select
	 	name as canonical_title,
		moduleid as canonical_moduleid,
		portal_type as canonical_type,
		module_ident as canonical_module_ident
	from modules
	where 'OpenStaxCollege' = any(authors) 
	and portal_type='Collection' ) as table2 on table2.canonical_module_ident = table1.derivative_parent;
	
	
--For cnx/#821 - query for all collection derivatives
--Revised of the above to get EACH authors information vs submitters information
select
	canonical.*,
	derivative.*,
  	persons.*
from (
	select 
	 	m.parent as derivative_parent,
		m.module_ident as derivative_module_ident,
		m.name as derivative_title,
		m.moduleid as derivative_colid,
		m.portal_type as derivative_type,
	    	m.created as created_at, 
		m.revised as last_revised,
		unnest(m.authors) as author
	from modules as m
	where m.parent is not null
	and m.portal_type = 'Collection') derivative
left join (
	select 
		p.personid,
		p.firstname as first_name, 
		p.surname, 
		p.email 
	from persons as p 
	where p.email is not null) persons on persons.personid = derivative.author
join 
	(select
	 	name as canonical_title,
		moduleid as canonical_moduleid,
		portal_type as canonical_type,
		module_ident as canonical_module_ident
	from modules
	where 'OpenStaxCollege' = any(authors) 
	and portal_type='Collection' ) as canonical on canonical.canonical_module_ident = derivative.derivative_parent
; 
