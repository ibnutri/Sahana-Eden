﻿# -*- coding: utf-8 -*-

module = 'budget'

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

# Parameters
# Only record 1 is used
resource = 'parameter'
table = module + '_' + resource
db.define_table(table,timestamp,uuidstamp,
                Field('shipping', 'double', default=15.00, notnull=True),
                Field('logistics', 'double', default=0.00, notnull=True),
                Field('admin', 'double', default=0.00, notnull=True),
                Field('indirect', 'double', default=7.00, notnull=True),
                migrate=migrate)
db[table].shipping.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].shipping.label = "Shipping cost"
db[table].logistics.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].logistics.label = "Procurement & Logistics cost"
db[table].admin.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].admin.label = "Administrative support cost"
db[table].indirect.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].indirect.label = "Indirect support cost HQ"
title_update = T('Edit Parameters')
s3.crud_strings[table] = Storage(title_update=title_update)

# Items
resource = 'item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('code', notnull=True, unique=True),
                Field('description', length=256, notnull=True),
                Field('cost_type', notnull=True),
                Field('category'),
                #Field('sub_category'),
                Field('unit_cost', 'double', default=0.00),
                Field('monthly_cost', 'double', default=0.00),
                Field('minute_cost', 'double', default=0.00),
                Field('megabyte_cost', 'double', default=0.00),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
db[table].description.requires = IS_NOT_EMPTY()
db[table].description.comment = SPAN("*", _class="req")
db[table].cost_type.requires = IS_IN_SET(['One-time', 'Recurring'])
db[table].category.requires = IS_IN_SET(['Consumable', 'Satellite', 'HF', 'VHF', 'Telephony', 'W-LAN', 'Network', 'Generator', 'Electrical', 'Vehicle', 'GPS', 'Tools', 'IT', 'ICT', 'TC', 'Stationery', 'Relief', 'Miscellaneous', 'Running Cost'])
#db[table].sub_category.requires = IS_IN_SET(['Satellite', 'VHF', 'UHF', 'HF', 'Airband', 'Telephony', 'GPS'])
title_create = T('Add Item')
title_display = T('Item Details')
title_list = T('List Items')
title_update = T('Edit Item')
title_search = T('Search Items')
subtitle_create = T('Add New Item')
subtitle_list = T('Items')
label_list_button = T('List Items')
label_create_button = T('Add Item')
label_search_button = T('Search Items')
msg_record_created = T('Item added')
msg_record_modified = T('Item updated')
msg_record_deleted = T('Item deleted')
msg_list_empty = T('No Items currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Kits
resource = 'kit'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('code', notnull=True, unique=True),
                Field('description', length=256),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('total_minute_cost', 'double', writable=False),
                Field('total_megabyte_cost', 'double', writable=False),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
db[table].total_minute_cost.label = "Total cost per minute"
db[table].total_megabyte_cost.label = "Total cost per Mbyte"
title_create = T('Add Kit')
title_display = T('Kit Details')
title_list = T('List Kits')
title_update = T('Edit Kit')
title_search = T('Search Kits')
subtitle_create = T('Add New Kit')
subtitle_list = T('Kits')
label_list_button = T('List Kits')
label_create_button = T('Add Kit')
msg_record_created = T('Kit added')
msg_record_modified = T('Kit updated')
msg_record_deleted = T('Kit deleted')
msg_list_empty = T('No Kits currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Kit<>Item Many2Many
resource = 'kit_item'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('kit_id', db.budget_kit),
                Field('item_id', db.budget_item, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                migrate=migrate)
db[table].kit_id.requires = IS_IN_DB(db, 'budget_kit.id', 'budget_kit.code')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select()[0].code
db[table].item_id.requires = IS_IN_DB(db, 'budget_item.id', 'budget_item.description')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.budget_item.id==item_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")

# Bundles
resource = 'bundle'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name', notnull=True, unique=True),
                Field('description', length=256),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].total_unit_cost.label = T('One time cost')
db[table].total_monthly_cost.label = T('Recurring cost')
title_create = T('Add Bundle')
title_display = T('Bundle Details')
title_list = T('List Bundles')
title_update = T('Edit Bundle')
title_search = T('Search Bundles')
subtitle_create = T('Add New Bundle')
subtitle_list = T('Bundles')
label_list_button = T('List Bundles')
label_create_button = T('Add Bundle')
msg_record_created = T('Bundle added')
msg_record_modified = T('Bundle updated')
msg_record_deleted = T('Bundle deleted')
msg_list_empty = T('No Bundles currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Bundle<>Kit Many2Many
resource = 'bundle_kit'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('bundle_id', db.budget_bundle),
                Field('kit_id', db.budget_kit, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('minutes', 'integer', default=0, notnull=True),
                Field('megabytes', 'integer', default=0, notnull=True),
                migrate=migrate)
db[table].bundle_id.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.description')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select()[0].description
db[table].kit_id.requires = IS_IN_DB(db, 'budget_kit.id', 'budget_kit.code')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select()[0].code
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].minutes.requires = IS_NOT_EMPTY()
db[table].minutes.label = T('Minutes per Month')
db[table].minutes.comment = SPAN("*", _class="req")
db[table].megabytes.requires = IS_NOT_EMPTY()
db[table].megabytes.label = T('Megabytes per Month')
db[table].megabytes.comment = SPAN("*", _class="req")

# Bundle<>Item Many2Many
resource = 'bundle_item'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('bundle_id', db.budget_bundle),
                Field('item_id', db.budget_item, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('minutes', 'integer', default=0, notnull=True),
                Field('megabytes', 'integer', default=0, notnull=True),
                migrate=migrate)
db[table].bundle_id.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.description')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select()[0].description
db[table].item_id.requires = IS_IN_DB(db, 'budget_item.id', 'budget_item.description')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.budget_item.id==item_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].minutes.requires = IS_NOT_EMPTY()
db[table].minutes.label = T('Minutes per Month')
db[table].minutes.comment = SPAN("*", _class="req")
db[table].megabytes.requires = IS_NOT_EMPTY()
db[table].megabytes.label = T('Megabytes per Month')
db[table].megabytes.comment = SPAN("*", _class="req")

# Staff Types
resource = 'staff'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name', notnull=True, unique=True),
                Field('grade', notnull=True),
                Field('salary', 'integer', notnull=True),
                Field('currency', notnull=True),
                Field('travel', 'integer', default=0),
                # Shouldn't be grade-dependent, but purely location-dependent
                #Field('subsistence', 'double', default=0.00),
                # Location-dependent
                #Field('hazard_pay', 'double', default=0.00),
                Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].grade.requires = IS_NOT_EMPTY()
db[table].grade.comment = SPAN("*", _class="req")
db[table].salary.requires = IS_NOT_EMPTY()
db[table].salary.label = T('Monthly Salary')
db[table].salary.comment = SPAN("*", _class="req")
db[table].currency.requires = IS_IN_SET(['Dollars', 'Euros', 'Pounds'])
title_create = T('Add Staff Type')
title_display = T('Staff Type Details')
title_list = T('List Staff Types')
title_update = T('Edit Staff Type')
title_search = T('Search Staff Types')
subtitle_create = T('Add New Staff Type')
subtitle_list = T('Staff Types')
label_list_button = T('List Staff Types')
label_create_button = T('Add Staff Type')
msg_record_created = T('Staff Type added')
msg_record_modified = T('Staff Type updated')
msg_record_deleted = T('Staff Type deleted')
msg_list_empty = T('No Staff Types currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Locations
resource = 'location'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('code', length=3, notnull=True, unique=True),
                Field('description'),
                Field('subsistence', 'double', default=0.00),
                Field('hazard_pay', 'double', default=0.00),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
# UN terminology
#db[table].subsistence.label = "DSA"
title_create = T('Add Location')
title_display = T('Location Details')
title_list = T('List Locations')
title_update = T('Edit Location')
title_search = T('Search Locations')
subtitle_create = T('Add New Location')
subtitle_list = T('Locations')
label_list_button = T('List Locations')
label_create_button = T('Add Location')
msg_record_created = T('Location added')
msg_record_modified = T('Location updated')
msg_record_deleted = T('Location deleted')
msg_list_empty = T('No Locations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Projects
resource = 'project'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('code', notnull=True, unique=True),
                Field('title'),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
title_create = T('Add Project')
title_display = T('Project Details')
title_list = T('List Projects')
title_update = T('Edit Project')
title_search = T('Search Projects')
subtitle_create = T('Add New Project')
subtitle_list = T('Projects')
label_list_button = T('List Projects')
label_create_button = T('Add Project')
msg_record_created = T('Project added')
msg_record_modified = T('Project updated')
msg_record_deleted = T('Project deleted')
msg_list_empty = T('No Projects currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Budgets
resource = 'budget'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name', notnull=True, unique=True),
                Field('description', length=256),
                Field('total_onetime_costs', 'double', writable=False),
                Field('total_recurring_costs', 'double', writable=False),
                Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
title_create = T('Add Budget')
title_display = T('Budget Details')
title_list = T('List Budgets')
title_update = T('Edit Budget')
title_search = T('Search Budgets')
subtitle_create = T('Add New Budget')
subtitle_list = T('Budgets')
label_list_button = T('List Budgets')
label_create_button = T('Add Budget')
msg_record_created = T('Budget added')
msg_record_modified = T('Budget updated')
msg_record_deleted = T('Budget deleted')
msg_list_empty = T('No Budgets currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Budget<>Bundle Many2Many
resource = 'budget_bundle'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('budget_id', db.budget_budget),
                Field('project_id', db.budget_project),
                Field('location_id', db.budget_location),
                Field('bundle_id', db.budget_bundle, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('months', 'integer', default=3, notnull=True),
                migrate=migrate)
db[table].budget_id.requires = IS_IN_DB(db, 'budget_budget.id', 'budget_budget.name')
db[table].budget_id.label = T('Budget')
db[table].budget_id.represent = lambda budget_id: db(db.budget_budget.id==budget_id).select()[0].name
db[table].project_id.requires = IS_IN_DB(db,'budget_project.id', 'budget_project.code')
db[table].project_id.label = T('Project')
db[table].project_id.represent = lambda project_id: db(db.budget_project.id==project_id).select()[0].code
db[table].location_id.requires = IS_IN_DB(db, 'budget_location.id', 'budget_location.code')
db[table].location_id.label = T('Location')
db[table].location_id.represent = lambda location_id: db(db.budget_location.id==location_id).select()[0].code
db[table].bundle_id.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.name')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select()[0].name
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].months.requires = IS_NOT_EMPTY()
db[table].months.label = T('Months')
db[table].months.comment = SPAN("*", _class="req")

# Budget<>Staff Many2Many
resource = 'budget_staff'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('budget_id', db.budget_budget),
                Field('project_id', db.budget_project),
                Field('location_id', db.budget_location),
                Field('staff_id', db.budget_staff, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('months', 'integer', default=3, notnull=True),
                migrate=migrate)
db[table].budget_id.requires = IS_IN_DB(db, 'budget_budget.id', 'budget_budget.name')
db[table].budget_id.label = T('Budget')
db[table].budget_id.represent = lambda budget_id: db(db.budget_budget.id==budget_id).select()[0].name
db[table].project_id.requires = IS_IN_DB(db,'budget_project.id', 'budget_project.code')
db[table].project_id.label = T('Project')
db[table].project_id.represent = lambda project_id: db(db.budget_project.id==project_id).select()[0].code
db[table].location_id.requires = IS_IN_DB(db, 'budget_location.id', 'budget_location.code')
db[table].location_id.label = T('Location')
db[table].location_id.represent = lambda location_id: db(db.budget_location.id==location_id).select()[0].code
db[table].staff_id.requires = IS_IN_DB(db, 'budget_staff.id', 'budget_staff.name')
db[table].staff_id.label = T('Staff')
db[table].staff_id.represent = lambda bundle_id: db(db.budget_staff.id==staff_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].months.requires = IS_NOT_EMPTY()
db[table].months.label = T('Months')
db[table].months.comment = SPAN("*", _class="req")

#resource = 'budget_equipment'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#                Field('name', notnull=True, unique=True),
#                Field('location', 'reference budget_location', ondelete='RESTRICT'),
#                Field('project', 'reference budget_project', ondelete='RESTRICT'),
#                Field('bundle', 'reference budget_bundle', ondelete='RESTRICT'),
#                Field('quantity', 'integer'),
#                Field('unit_cost', 'double', writable=False),
#                Field('months', 'integer'),
#                Field('monthly_cost', 'double', writable=False),
#                Field('total_unit_cost', writable=False),
#                Field('total_monthly_cost', writable=False),
#                Field('comments', length=256),
#                migrate=migrate)
#db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
#db[table].name.comment = SPAN("*", _class="req")
#db[table].location.requires = IS_IN_DB(db, 'budget_location.id', 'budget_location.code')
#db[table].location.comment = SPAN("*", _class="req")
#db[table].project.requires = IS_IN_DB(db,'budget_project.id', 'budget_project.code')
#db[table].project.comment = SPAN("*",_class="req")
#db[table].bundle.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.name')
#db[table].bundle.comment = SPAN("*", _class="req")
#title_create = T('Add Equipment Budget')
#title_display = T('Equipment Budget Details')
#title_list = T('List Equipment Budgets')
#title_update = T('Edit Equipment Budget')
#title_search = T('Search Equipment Budgets')
#subtitle_create = T('Add New Equipment Budget')
#subtitle_list = T('Equipment Budgets')
#label_list_button = T('List Equipment Budgets')
#label_create_button = T('Add Equipment Budget')
#msg_record_created = T('Equipment Budget added')
#msg_record_modified = T('Equipment Budget updated')
#msg_record_deleted = T('Equipment Budget deleted')
#msg_list_empty = T('No Equipment Budgets currently registered')
#s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#resource = 'budget_staff'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#                Field('name', notnull=True, unique=True),
#                Field('location', 'reference budget_location', ondelete='RESTRICT'),
#                Field('project', 'reference budget_project', ondelete='RESTRICT'),
#                Field('job_title', 'reference budget_staff', ondelete='RESTRICT'),
#                Field('grade', writable=False),
#                Field('type'),
#                Field('headcount', 'integer'),
#                Field('months', 'integer'),
#                Field('salary', writable=False),
#                Field('travel', writable=False),
#                Field('subsistence', 'double', writable=False),
#                Field('hazard_pay', 'double', writable=False),
#                Field('total', 'double', writable=False),
#                Field('comments', length=256),
#                migrate=migrate)
#db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
#db[table].name.comment = SPAN("*", _class="req")
#db[table].location.requires = IS_IN_DB(db, 'budget_location.id', 'budget_location.code')
#db[table].location.comment = SPAN("*", _class="req")
#db[table].project.requires = IS_IN_DB(db, 'budget_project.id', 'budget_project.code')
#db[table].job_title.requires = IS_IN_DB(db, 'budget_staff.id', 'budget_staff.name')
#db[table].job_title.comment = SPAN("*", _class="req")
#db[table].project.comment = SPAN("*", _class="req")
#db[table].type.requires = IS_IN_SET(['Staff', 'Consultant'])
#title_create = T('Add Staff Budget')
#title_display = T('Staff Budget Details')
#title_list = T('List Staff Budgets')
#title_update = T('Edit Staff Budget')
#title_search = T('Search Staff Budgets')
#subtitle_create = T('Add New Staff Budget')
#subtitle_list = T('Staff Budgets')
#label_list_button = T('List Staff Budgets')
#label_create_button = T('Add Staff Budget')
#msg_record_created = T('Staff Budget added')
#msg_record_modified = T('Staff Budget updated')
#msg_record_deleted = T('Staff Budget deleted')
#msg_list_empty = T('No Staff Budgets currently registered')
#s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
