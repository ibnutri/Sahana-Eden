# -*- coding: utf-8 -*-

#
# Person Registry (VITA)
#
# created 2009-07-15 by nursix
#

module = 'pr'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

#
# Person Entities
# A person entity represents the logical appearance of persons, which can be individuals
# or groups. 
#
resource = 'person'                                     # rename into pentity
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('is_group', 'boolean'),           # Replace by opt_pentity_type
                Field('first_name', notnull=True),      # Group names go here
                Field('middle_name'),
                Field('last_name'),
                Field('preferred_name'),
                Field('email', unique=True),            # Needed for AAA (change this!)
                Field('mobile_phone'),                  # Needed for SMS (change this!)
                Field('address', 'text'),               # move to address data
                Field('postcode'),                      # move to address data
                Field('website'),                       # to be removed (goes into contacts)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN("*", _class="req")
#db[table].last_name.label = T("Family Name")
db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].mobile_phone.label = T("Mobile Phone #")
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].website.requires = IS_NULL_OR(IS_URL())
title_create = T('Add Person')
title_display = T('Person Details')
title_list = T('List People')
title_update = T('Edit Person')
title_search = T('Search People')
subtitle_create = T('Add New Person')
subtitle_list = T('People')
label_list_button = T('List People')
label_create_button = T('Add Person')
msg_record_created = T('Person added')
msg_record_modified = T('Person updated')
msg_record_deleted = T('Person deleted')
msg_list_empty = T('No People currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
person_id = SQLTable(None, 'person_id',
            Field('person_id', db.pr_person,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s')),
                represent = lambda id: (id and [db(db.pr_person.id==id).select()[0].first_name] or ["None"])[0],
                comment = DIV(A(T('Add Contact'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Contact|The Person to contact for this."))),
                ondelete = 'RESTRICT'
                ))

#
# Person-Identity
# An identity is a unique code assigned to an individual person in a person registry.
# This table is to track official identities of individuals in the Sahana Person Registry.
#
resource='id_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('name')
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(name = "Passport")
   db[table].insert(name = "National ID Card")
   db[table].insert(name = "Driving License")

# Reusable field for other tables to reference
opt_id_type = SQLTable(None, 'opt_id_type',
                db.Field('id_type', db.pr_id_type,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_id_type.id', 'pr_id_type.name')),
                represent = lambda id: (id and [db(db.pr_id_type.id==id).select()[0].name] or ["None"])[0],
                comment = None,
                ondelete = 'RESTRICT'
                ))

resource = 'identity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                person_id,                          # Reference to person
                opt_id_type,                        # ID type
                Field('value'),                     # ID value
                Field('ia_name'),                   # Name of issuing authority
#                Field('ia_subdivision'),            # Name of issuing authority subdivision
#                Field('ia_code'),                   # Code of issuing authority (if any)
                Field('comment'))                   # a comment (optional)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].ia_name.label = T("Issuing Authority")

# Contacts
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name'),   # Contact type
                Field('value', notnull=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_IN_SET(['phone', 'fax', 'skype', 'msn', 'yahoo'])
db[table].value.requires = IS_NOT_EMPTY()
title_create = T('Add Contact Detail')
title_display = T('Contact Details')
title_list = T('List Contact Details')
title_update = T('Edit Contact Detail')
title_search = T('Search Contact Details')
subtitle_create = T('Add New Contact Detail')
subtitle_list = T('Contact Details')
label_list_button = T('List Contact Details')
label_create_button = T('Add Contact Detail')
msg_record_created = T('Contact Detail added')
msg_record_modified = T('Contact Detail updated')
msg_record_deleted = T('Contact Detail deleted')
msg_list_empty = T('No Contact Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contacts to People
resource = 'contact_to_person'
table = module + '_' + resource
db.define_table(table,timestamp,
                Field('person_id', db.pr_person),
                Field('contact_id', db.pr_contact),
                migrate=migrate)
db[table].person_id.label = 'Person'
db[table].contact_id.requires = IS_IN_DB(db, 'pr_contact.id', 'pr_contact.name')
db[table].contact_id.label = 'Contact Detail'