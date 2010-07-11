# -*- coding: utf-8 -*-

"""
    S3 Person Registry

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
"""

module = "pr"

# *****************************************************************************
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

# *****************************************************************************
# PersonEntity (pentity)
#
opt_pr_entity_type = db.Table(None, "opt_pr_entity_type",
                              Field("opt_pr_entity_type", "integer",
                                    requires = IS_IN_SET(vita.trackable_types, zero=None),
                                    default = vita.DEFAULT_TRACKABLE,
                                    label = T("Entity Type"),
                                    represent = lambda opt:
                                        vita.trackable_types.get(opt, UNKNOWN_OPT)))


# -----------------------------------------------------------------------------
#
def shn_pentity_represent(id, default_label="[no label]"):

    """
        Represent a Person Entity in option fields or list views
    """

    pentity_str = default = T("None (no such record)")

    table = db.pr_pentity
    pentity = db(table.id == id).select(
        table.opt_pr_entity_type,
        table.label,
        limitby=(0, 1)).first()
    if not pentity:
        return default
    entity_type = pentity.opt_pr_entity_type
    label = pentity.label or default_label

    etype = lambda entity_type: vita.trackable_types[entity_type]

    if entity_type == 1:
        # Person
        table = db.pr_person
        person = db(table.pr_pe_id == id).select(
                    table.first_name,
                    table.middle_name,
                    table.last_name,
                    limitby=(0, 1))
        if person:
            person = person.first()
            pentity_str = "%s %s (%s)" % (
                vita.fullname(person),
                label,
                etype(entity_type)
            )

    elif entity_type == 2:
        # Group
        table = db.pr_group
        group = db(table.pr_pe_id == id).select(
                    table.group_name,
                    limitby=(0, 1))
        if group:
            group = group.first()
            pentity_str = "%s (%s)" % (
                group.group_name,
                vita.trackable_types[entity_type]
            )

    elif entity_type == 5:
        # Organisation
        table = db.org_organisation
        organisation = db(table.pr_pe_id == id).select(
                    table.name,
                    limitby=(0, 1))
        if organisation:
            organisation = organisation.first()
            pentity_str = "%s (%s)" % (
                organisation.name,
                vita.trackable_types[entity_type]
            )

    elif entity_type == 6:
        # Office
        table = db.org_office
        office = db(table.pr_pe_id == id).select(
                    table.name,
                    limitby=(0, 1))
        if office:
            office = office.first()
            pentity_str = "%s (%s)" % (
                office.name,
                vita.trackable_types[entity_type]
            )

    else:
        pentity_str = "[%s] (%s)" % (
            label,
            vita.trackable_types[entity_type]
        )

    return pentity_str

# -----------------------------------------------------------------------------
#
resource = "pentity"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
#                    Field("parent"),                # Parent Entity
                    opt_pr_entity_type,              # Entity class
                    Field("label", length=128),      # Recognition Label
                    migrate=migrate)

# Field validation
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#table.label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_pentity.label"))
#table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent))

# Field representation
#table.deleted.readable = True

# Field labels
#table.parent.label = T("belongs to")

# CRUD Strings

#
# Reusable field for other tables to reference --------------------------------
#
pr_pe_id = db.Table(None, "pr_pe_id",
                Field("pr_pe_id", db.pr_pentity,
                    requires =  IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = "RESTRICT",
                    label = T("ID")
                ))

#
# Person Entity Field Set -----------------------------------------------------
#
pr_pe_fieldset = db.Table(None, "pr_pe_fieldset",
                    Field("pr_pe_id", db.pr_pentity,
                        requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent)),
                        represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                        ondelete = "RESTRICT",
                        readable = False,   # should be invisible in (most) forms
                        writable = False    # should be invisible in (most) forms
                    ),
                    #Field("pr_pe_parent", db.pr_pentity,
                        #requires =  IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent)),
                        #represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                        #ondelete = "RESTRICT",
                        #label = T("belongs to"),
                        #readable = False,   # should be invisible in (most) forms
                        #writable = False    # should be invisible in (most) forms
                    #),
                    Field("pr_pe_label", length=128,
                        label = T("ID Label"),
                        requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_pentity.label"))
                    )) # Can't be unique if we allow Null!

# -----------------------------------------------------------------------------
#
def shn_pentity_ondelete(record):

    """
        Deletes pr_pentity entries, when a subentity is deleted, used as
        delete_onaccept callback.

        crud.settings.delete_onaccept = shn_pentity_ondelete
    """

    if "pr_pe_id" in record:
        pr_pe_id = record.pr_pe_id

        delete_onvalidation = crud.settings.delete_onvalidation
        delete_onaccept = crud.settings.delete_onaccept

        crud.settings.delete_onvalidation = None
        crud.settings.delete_onaccept = None

        if db(db.s3_setting.id == 1).select(db.s3_setting.archive_not_delete, limitby=(0, 1)).first().archive_not_delete:
            db(db.pr_pentity.id == pr_pe_id).update(deleted = True)
        else:
            crud.delete(db.pr_pentity, pr_pe_id)

        # TODO: delete joined resources!?

        crud.settings.delete_onvalidation = delete_onvalidation
        crud.settings.delete_onaccept = delete_onaccept

    return True


def shn_pentity_onaccept(form, table=None, entity_type=1):

    """
        Adds or updates a pr_pentity entries as necessary, used as
        onaccept-callback for create/update of subentities.
    """

    if "pr_pe_id" in table.fields:
        record = db(table.id == form.vars.id).select(table.pr_pe_id, table.pr_pe_label, limitby=(0, 1)).first()
        if record:
            pr_pe_id = record.pr_pe_id
            label = record.pr_pe_label
            if pr_pe_id:
                # update action
                db(db.pr_pentity.id == pr_pe_id).update(label=label)
            else:
                # create action
                pr_pe_id = db.pr_pentity.insert(opt_pr_entity_type=entity_type,
                                                label=label)
                if pr_pe_id:
                    db(table.id == form.vars.id).update(pr_pe_id=pr_pe_id)

    return True

# *****************************************************************************
# Person (person)
#

# -----------------------------------------------------------------------------
# Gender
#
pr_person_gender_opts = {
    1:T("unknown"),
    2:T("female"),
    3:T("male")
    }

opt_pr_gender = db.Table(None, "opt_pr_gender",
                    Field("opt_pr_gender", "integer",
                        requires = IS_IN_SET(pr_person_gender_opts, zero=None),
                        default = 1,
                        label = T("Gender"),
                        represent = lambda opt: pr_person_gender_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Age Group
#
pr_person_age_group_opts = {
    1:T("unknown"),
    2:T("Infant (0-1)"),
    3:T("Child (2-11)"),
    4:T("Adolescent (12-20)"),
    5:T("Adult (21-50)"),
    6:T("Senior (50+)")
    }

opt_pr_age_group = db.Table(None, "opt_pr_age_group",
                    Field("opt_pr_age_group", "integer",
                        requires = IS_IN_SET(pr_person_age_group_opts, zero=None),
                        default = 1,
                        label = T("Age Group"),
                        represent = lambda opt:
                            pr_person_age_group_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Marital Status
#
pr_marital_status_opts = {
    1:T("unknown"),
    2:T("single"),
    3:T("married"),
    4:T("separated"),
    5:T("divorced"),
    6:T("widowed"),
    99:T("other")
}

opt_pr_marital_status = db.Table(None, "opt_pr_marital_status",
                        Field("opt_pr_marital_status", "integer",
                            requires = IS_NULL_OR(IS_IN_SET(pr_marital_status_opts)),
                            default = 1,
                            label = T("Marital Status"),
                            represent = lambda opt:
                                opt and pr_marital_status_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Religion
#
pr_religion_opts = {
    1:T("none"),
    2:T("Christian"),
    3:T("Muslim"),
    4:T("Jew"),
    5:T("Bhuddist"),
    6:T("Hindu"),
    99:T("other")
    }

opt_pr_religion = db.Table(None, "opt_pr_religion",
                    Field("opt_pr_religion", "integer",
                        requires = IS_NULL_OR(IS_IN_SET(pr_religion_opts)),
                        # default = 1,
                        label = T("Religion"),
                        represent = lambda opt: pr_religion_opts.get(opt, UNKNOWN_OPT)))

#
# Nationality and Country of Residence ----------------------------------------
#
pr_nationality_opts = shn_list_of_nations

opt_pr_nationality = db.Table(None, "opt_pr_nationality",
                        Field("opt_pr_nationality", "integer",
                            requires = IS_NULL_OR(IS_IN_SET(pr_nationality_opts)),
                            # default = 999, # unknown
                            label = T("Nationality"),
                            represent = lambda opt: pr_nationality_opts.get(opt, UNKNOWN_OPT)))

opt_pr_country = db.Table(None, "opt_pr_country",
                        Field("opt_pr_country", "integer",
                            requires = IS_NULL_OR(IS_IN_SET(pr_nationality_opts)),
                            # default = 999, # unknown
                            label = T("Country of Residence"),
                            represent = lambda opt: pr_nationality_opts.get(opt, UNKNOWN_OPT)))

#
# shn_pr_person_represent -----------------------------------------------------
#
def shn_pr_person_represent(id):

    def _represent(id):
        table = db.pr_person
        person = db(table.id == id).select(
                    table.first_name,
                    table.middle_name,
                    table.last_name,
                    limitby=(0, 1))
        if person:
            return vita.fullname(person.first())
        else:
            return None

    name = cache.ram("pr_person_%s" % id, lambda: _represent(id), time_expire=10)
    return name

#
# person table ----------------------------------------------------------------
#
resource = "person"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
                Field("missing", "boolean", default=False), # Missing?
                Field("first_name", notnull=True),      # first or only name
                Field("middle_name"),                   # middle name
                Field("last_name"),                     # last name
                Field("preferred_name"),                # how the person uses to be called
                Field("local_name"),                    # name in local language and script, Sahana legacy
                opt_pr_gender,
                opt_pr_age_group,
                # Person Details
                Field("date_of_birth", "date"),         # Sahana legacy
                opt_pr_nationality,                     # Nationality
                opt_pr_country,                         # Country of residence
                opt_pr_religion,                        # Sahana legacy
                opt_pr_marital_status,                  # Sahana legacy
                Field("occupation"),                    # Sahana legacy
                Field("comment"),                       # comment
                migrate=migrate)

# Field validation
table.date_of_birth.requires = IS_NULL_OR(IS_DATE_IN_RANGE(maximum=request.utcnow.date(),
                                        error_message="%s " % T("Enter a date before") + "%(max)s!"))
table.first_name.requires = IS_NOT_EMPTY()   # People don"t have to have unique names, some just have a single name
table.pr_pe_label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_person.pr_pe_label"))

# Field representation
table.pr_pe_label.comment = DIV(DIV(_class="tooltip",
    _title=T("ID Label|Number or Label on the identification tag this person is wearing (if any).")))
table.first_name.comment =  DIV(SPAN("*", _class="req", _style="padding-right: 5px;"), DIV(_class="tooltip",
    _title=T("First name|The first or only name of the person (mandatory).")))
table.preferred_name.comment = DIV(DIV(_class="tooltip",
    _title=T("Preferred Name|The name to be used when calling for or directly addressing the person (optional).")))
table.local_name.comment = DIV(DIV(_class="tooltip",
    _title=T("Local Name|Name of the person in local language and script (optional).")))
table.opt_pr_nationality.comment = DIV(DIV(_class="tooltip",
    _title=T("Nationality|Nationality of the person.")))
table.opt_pr_country.comment = DIV(DIV(_class="tooltip",
    _title=T("Country of Residence|The country the person usually lives in.")))

table.missing.represent = lambda missing: (missing and ["missing"] or [""])[0]

# Field labels
table.opt_pr_gender.label = T("Gender")
table.opt_pr_age_group.label = T("Age group")

# CRUD Strings
ADD_PERSON = T("Add Person")
LIST_PERSONS = T("List Persons")
s3.crud_strings[tablename] = Storage(
    title_create = T("Add a Person"),
    title_display = T("Person Details"),
    title_list = LIST_PERSONS,
    title_update = T("Edit Person Details"),
    title_search = T("Search Persons"),
    subtitle_create = ADD_PERSON,
    subtitle_list = T("Persons"),
    label_list_button = LIST_PERSONS,
    label_create_button = ADD_PERSON,
    label_delete_button = T("Delete Person"),
    msg_record_created = T("Person added"),
    msg_record_modified = T("Person details updated"),
    msg_record_deleted = T("Person deleted"),
    msg_list_empty = T("No Persons currently registered"))

#
# person_id: reusable field for other tables to reference ---------------------
#
shn_person_comment = DIV(A(ADD_PERSON,
                           _class="colorbox",
                           _href=URL(r=request, c="pr", f="person", args="create", vars=dict(format="popup")),
                           _target="top",
                           _title=ADD_PERSON),
                         DIV(DIV(_class="tooltip",
                              _title=Tstr("Person") + "|" + Tstr("Select the person associated with this scenario.")))
                                 )

person_id = db.Table(None, "person_id",
                FieldS3("person_id", db.pr_person, sortby=["first_name", "middle_name", "last_name"],
                    requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent)),
                    represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0],
                    comment = shn_person_comment,
                    ondelete = "RESTRICT"
                ))

s3xrc.model.configure(table,
                      onaccept=lambda form: \
                      shn_pentity_onaccept(form, table=db.pr_person, entity_type=1),
                      delete_onaccept=lambda form: \
                      shn_pentity_ondelete(form),
                      list_fields = ["id",
                                     "first_name",
                                     "middle_name",
                                     "last_name",
                                     "date_of_birth",
                                     "opt_pr_nationality",
                                     "missing"])

# *****************************************************************************
# Group (group)
#

#
# Group types -----------------------------------------------------------------
#
pr_group_type_opts = {
    1:T("Family"),
    2:T("Tourist Group"),
    3:T("Relief Team"),
    4:T("other")
    }

opt_pr_group_type = db.Table(None, "opt_pr_group_type",
                             Field("opt_pr_group_type", "integer",
                                   requires = IS_IN_SET(pr_group_type_opts, zero=None),
                                   default = 4,
                                   label = T("Group Type"),
                                   represent = lambda opt: pr_group_type_opts.get(opt, UNKNOWN_OPT)))

#
# group table -----------------------------------------------------------------
#
resource = "group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                pr_pe_fieldset,                                 # Person Entity Field Set
                opt_pr_group_type,                              # group type
                Field("system","boolean",default=False),        # System internal? (e.g. users?)
                Field("group_name"),                            # Group name (optional? => No!)
                Field("group_description"),                     # Group short description
#                Field("group_head"),                           # Sahana legacy
#                Field("no_of_adult_males", "integer"),         # Sahana legacy
#                Field("no_of_adult_females", "integer"),       # Sahana legacy
#                Field("no_of_children", "integer"),            # Sahana legacy
#                Field("no_of_children_males", "integer"),      # by Khushbu
#                Field("no_of_children_females", "integer"),    # by Khushbu
#                Field("no_of_displaced", "integer"),           # Sahana legacy
#                Field("no_of_missing", "integer"),             # Sahana legacy
#                Field("no_of_dead", "integer"),                # Sahana legacy
#                Field("no_of_rehabilitated", "integer"),       # Sahana legacy
#                Field("checklist", "text"),                    # Sahana legacy
#                Field("description", "text"),                  # Sahana legacy
                Field("comment"),                               # optional comment
                migrate=migrate)

table.pr_pe_label.readable = False
table.pr_pe_label.writable = False
table.system.readable = False
table.system.writable = False
table.pr_pe_label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_group.pr_pe_label"))
table.opt_pr_group_type.label = T("Group type")
table.group_name.label = T("Group name")
table.group_name.requires = IS_NOT_EMPTY()
table.group_name.comment = DIV(SPAN("*", _class="req", _style="padding-right: 5px;"))
table.group_description.label = T("Group description")

# CRUD Strings
ADD_GROUP = T("Add Group")
LIST_GROUPS = T("List Groups")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_GROUP,
    title_display = T("Group Details"),
    title_list = LIST_GROUPS,
    title_update = T("Edit Group"),
    title_search = T("Search Groups"),
    subtitle_create = T("Add New Group"),
    subtitle_list = T("Groups"),
    label_list_button = LIST_GROUPS,
    label_create_button = ADD_GROUP,
    label_delete_button = T("Delete Group"),
    msg_record_created = T("Group added"),
    msg_record_modified = T("Group updated"),
    msg_record_deleted = T("Group deleted"),
    msg_list_empty = T("No Groups currently registered"))

#
# group_id: reusable field for other tables to reference ----------------------
#
group_id = db.Table(None, "group_id",
                FieldS3("group_id", db.pr_group, sortby="group_name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id", "%(id)s: %(group_name)s", filterby="system", filter_opts=(False,))),
                    represent = lambda id: (id and [db(db.pr_group.id==id).select()[0].group_name] or ["None"])[0],
                    comment = DIV(A(s3.crud_strings.pr_group.label_create_button,
                                    _class="colorbox",
                                    _href=URL(r=request, c="pr", f="group", args="create", vars=dict(format="popup")),
                                    _target="top",
                                    _title=s3.crud_strings.pr_group.label_create_button),
                                  DIV(DIV(_class="tooltip",
                                          _title=T("Create Group Entry|Create a group entry in the registry.")))),
                    ondelete = "RESTRICT"))

s3xrc.model.configure(table,
    onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_group, entity_type=2),
    delete_onaccept=lambda form: shn_pentity_ondelete(form))

# *****************************************************************************
# Group membership (group_membership)
#
resource = "group_membership"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, deletion_status,
                group_id,
                person_id,
                Field("group_head", "boolean", default=False),
                Field("description"),
                Field("comment"),
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(pr_group="group_id",
                                      pr_person="person_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields=["id",
                                   "group_id",
                                   "person_id",
                                   "group_head",
                                   "description"])

# Field validation

# Field representation
table.group_head.represent = lambda group_head: (group_head and [T("yes")] or [""])[0]

# Field labels

# CRUD Strings
if request.function in ("person", "group_membership"):
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Membership"),
        title_display = T("Membership Details"),
        title_list = T("Memberships"),
        title_update = T("Edit Membership"),
        title_search = T("Search Membership"),
        subtitle_create = T("Add New Membership"),
        subtitle_list = T("Current Memberships"),
        label_list_button = T("List All Memberships"),
        label_create_button = T("Add Membership"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Membership added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Memberships currently registered"))
elif request.function == "group":
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Group Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Group Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Group Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

# *****************************************************************************
# Functions:
#
def shn_pr_person_search_simple(xrequest, **attr):

    """
        Simple search form for persons
    """

    if attr is None:
        attr = {}

    table = db.pr_person

    if not shn_has_permission("read", table):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, args="search_simple", vars=request.vars)}))

    if xrequest.representation == "html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f="person", args="[id]"))

        # Custom view
        response.view = "%s/person_search.html" % xrequest.prefix

        # Title and subtitle
        title = T("Search for a Person")
        subtitle = T("Matching Records")

        # Select form
        form = FORM(TABLE(
                TR(T("Name and/or ID Label: "),
                   INPUT(_type="text", _name="label", _size="40"),
                   DIV(DIV(_class="tooltip",
                           _title=T("Name and/or ID Label|To search for a person, enter any of the first, middle or last names and/or the ID label of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons.")))),
                TR("", INPUT(_type="submit", _value="Search"))))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = s3xrc.search_simple(db.pr_person,
                fields = ["pr_pe_label", "first_name", "middle_name", "last_name"],
                label = form.vars.label)

            if results and len(results):
                query = table.id.belongs(results)
            else:
                query = (table.id == 0)
                rows = None

            # Add filter
            if response.s3.filter:
                response.s3.filter = (response.s3.filter) & (query)
            else:
                response.s3.filter = (query)

            xrequest.id = None

            # Get report from HTML exporter
            report = shn_list(xrequest, listadd=False)

            output.update(dict(report))

        # Title and subtitle
        title = T("List of persons")
        subtitle = T("Matching Records")
        output.update(title=title, subtitle=subtitle)

        # Custom view
        response.view = "%s/person_search.html" % xrequest.prefix

        try:
            label_create_button = s3.crud_strings["pr_person"].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f="person", args="create"), _class="action-btn")

        output.update(add_btn=add_btn)
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, "person", method="search_simple", action=shn_pr_person_search_simple )

# -----------------------------------------------------------------------------
#
def shn_pr_rheader(jr, tabs=[]):

    """ Person Registry page headers """

    if jr.representation == "html":

        rheader_tabs = shn_rheader_tabs(jr, tabs)

        if jr.name == "person":

            _next = jr.here()
            _same = jr.same()

            person = jr.record

            if person:
                rheader = DIV(TABLE(

                    TR(TH(T("Name: ")),
                       vita.fullname(person),
                       TH(T("ID Label: ")),
                       "%(pr_pe_label)s" % person),

                    TR(TH(T("Date of Birth: ")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH(T("Gender: ")),
                       "%s" % pr_person_gender_opts.get(person.opt_pr_gender, T("unknown"))),

                    TR(TH(T("Nationality: ")),
                       "%s" % pr_nationality_opts.get(person.opt_pr_nationality, T("unknown")),
                       TH(T("Age Group: ")),
                       "%s" % pr_person_age_group_opts.get(person.opt_pr_age_group, T("unknown"))),

                    #))
                    ), rheader_tabs)

                return rheader

        elif jr.name == "group":

            _next = jr.here()
            _same = jr.same()

            group = jr.record

            if group:
                rheader = DIV(TABLE(

                    TR(TH(T("Name: ")),
                       group.group_name,
                       TH(""),
                       ""),
                    TR(TH(T("Description: ")),
                       group.group_description,
                       TH(""),
                       "")

                    ), rheader_tabs)

                return rheader

    return None

#
# END
# *****************************************************************************
