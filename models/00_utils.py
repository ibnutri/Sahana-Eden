# -*- coding: utf-8 -*-

""" Utilities """

# *****************************************************************************
# Session

def s3_sessions():

    """ Extend session to support:
            Multiple flash classes
            Roles caching
            Settings
                Debug mode
                Security mode
                Audit modes

    """

    response.error = session.error
    response.confirmation = session.confirmation
    response.warning = session.warning
    session.error = []
    session.confirmation = []
    session.warning = []

    roles = []
    if auth.is_logged_in():
        user_id = auth.user.id
        _memberships = db.auth_membership
        memberships = db(_memberships.user_id == user_id).select(_memberships.group_id) # Cache this & invalidate when memberships are changed?
        roles = [m.group_id for m in memberships]
    session.s3.roles = roles

    # Are we running in debug mode?
    session.s3.debug = request.vars.get("debug", None) or deployment_settings.get_base_debug()

    # Should we use Content-Delivery Networks?
    session.s3.cdn = deployment_settings.get_base_cdn()

    # Security Policy
    #session.s3.self_registration = deployment_settings.get_security_self_registration()
    session.s3.security_policy = deployment_settings.get_security_policy()

    # We Audit if either the Global or Module asks us to
    # (ignore gracefully if module author hasn't implemented this)
    try:
        session.s3.audit_read = deployment_settings.get_security_audit_read() \
            or deployment_settings.modules[request.controller].get("audit_read", False)
        session.s3.audit_write = deployment_settings.get_security_audit_write() \
            or deployment_settings.modules[request.controller].get("audit_write", False)
    except:
        # Controller doesn't link to a 'module' (e.g. appadmin)
        session.s3.audit_read = False
        session.s3.audit_write = False

    return

# Extend the session
s3_sessions()

# *****************************************************************************
# Utilities

super_entity = s3xrc.model.super_entity
super_link = s3xrc.model.super_link
super_key = s3xrc.model.super_key

def s3_debug(message, value=None):

    """ Debug Function (same name/parameters as JavaScript one)

        Provide an easy, safe, systematic way of handling Debug output
        (print to stdout doesn't work with WSGI deployments)

    """

    import sys
    try:
        output = "S3 Debug: " + str(message)
        if value:
            output += ": " + str(value)
    except:
        output = "S3 Debug: " + unicode(message)
        if value:
            output += ": " + unicode(value)

    print >> sys.stderr, output


# -----------------------------------------------------------------------------
def s3_get_utc_offset():

    """ Get the current UTC offset for the client """

    offset = None

    if auth.is_logged_in():
        # 1st choice is the personal preference (useful for GETs if user wishes to see times in their local timezone)
        offset = session.auth.user.utc_offset
        if offset:
            offset = offset.strip()

    if not offset:
        # 2nd choice is what the client provides in the hidden field (for form POSTs)
        offset = request.post_vars.get("_utc_offset", None)
        if offset:
            offset = int(offset)
            utcstr = offset < 0 and "UTC +" or "UTC -"
            hours = abs(int(offset/60))
            minutes = abs(int(offset % 60))
            offset = "%s%02d%02d" % (utcstr, hours, minutes)

    if not offset:
        # 3rd choice is the server default (what most clients should see the timezone as)
        offset = deployment_settings.L10n.utc_offset

    return offset

# Store last value in session
session.s3.utc_offset = s3_get_utc_offset()


# -----------------------------------------------------------------------------
def shn_user_utc_offset():

    """ for backward compatibility """
    return session.s3.utc_offset


# -----------------------------------------------------------------------------
def shn_as_local_time(value):
    """
        represents a given UTC datetime.datetime object as string:

        - for the local time of the user, if logged in
        - as it is in UTC, if not logged in, marked by trailing +0000
    """

    format="%Y-%m-%d %H:%M:%S"

    offset = IS_UTC_OFFSET.get_offset_value(session.s3.utc_offset)

    if offset:
        dt = value + datetime.timedelta(seconds=offset)
        return dt.strftime(str(format))
    else:
        dt = value
        return dt.strftime(str(format))+" +0000"


# -----------------------------------------------------------------------------
# Phone number requires
# @ToDo Support ',' & '/' to separate multiple phone numbers
shn_phone_requires = IS_NULL_OR(IS_MATCH('\+?\s*[\s\-\.\(\)\d]+(?:(?: x| ext)\s?\d{1,5})?$'))


# -----------------------------------------------------------------------------
# Make URLs clickable
shn_url_represent = lambda url: (url and [A(url, _href=url, _target="blank")] or [""])[0]


# -----------------------------------------------------------------------------
#def myname(user_id):

    #""" Return the first name of the current user """

    #user = db.auth_user[user_id]
    #return user.first_name if user else NONE


# -----------------------------------------------------------------------------
def s3_logged_in_person():

    """ Get the person ID of the current user """

    if auth.shn_logged_in():
        person = db.pr_person
        record = db(person.uuid == session.auth.user.person_uuid).select(
                    person.id, limitby=(0,1)).first()
        if record:
            return record.id

    return None

# -----------------------------------------------------------------------------
def unauthorised():

    """ Redirection upon unauthorized request (interactive!) """

    session.error = T("Not Authorised!")
    redirect(URL(r=request, c="default", f="user", args="login"))


# -----------------------------------------------------------------------------
def shn_abbreviate(word, size=48):

    """ Abbreviate a string. For use as a .represent

        see also: vita.truncate(self, text, length=48, nice=True)

    """

    if word:
        if (len(word) > size):
            word = "%s..." % word[:size - 4]
        else:
            return word
    else:
        return word


# -----------------------------------------------------------------------------
def shn_action_buttons(r,
                       deletable=True,
                       copyable=False,
                       read_url=None,
                       update_url=None,
                       delete_url=None,
                       copy_url=None):

    """ Provide the usual Action Buttons for Column views.
        Allow customizing the urls, since this overwrites anything
        that would be inserted by shn_list via linkto.  The resource
        id should be represented by "[id]".

        Designed to be called from a postp

        @note: standard action buttons will be inserted automatically

    """

    if r.component:
        args = [r.component_name, "[id]"]
    else:
        args = ["[id]"]

    if shn_has_permission("update", r.table):
        if not update_url:
            update_url = str(URL(r=request, args = args + ["update"]))
        response.s3.actions = [
            dict(label=str(UPDATE), _class="action-btn", url=update_url),
        ]
        # Provide the ability to delete records in bulk
        if deletable and shn_has_permission("delete", r.table):
            if not delete_url:
                delete_url = str(URL(r=request, args = args + ["delete"]))
            response.s3.actions.append(
                dict(label=str(DELETE), _class="delete-btn", url=delete_url)
            )
        if copyable:
            if not copy_url:
                copy_url = str(URL(r=request, args = args + ["copy"]))
            response.s3.actions.append(
                dict(label=str(COPY), _class="action-btn", url=copy_url)
            )
    else:
        if not read_url:
            read_url = str(URL(r=request, args = args))
        response.s3.actions = [
            dict(label=str(READ), _class="action-btn", url=read_url)
        ]

    return


# -----------------------------------------------------------------------------
def shn_compose_message(data, template):

    """ Compose an SMS Message from an XSLT

        from FRP

    """

    if data:
        root = etree.Element("message")
        for k in data.keys():
            entry = etree.SubElement(root, k)
            entry.text = s3xrc.xml.xml_encode(str(data[k]))

        message = None
        tree = etree.ElementTree(root)

        if template:
            template = os.path.join(request.folder, "static", template)
            if os.path.exists(template):
                message = s3xrc.xml.transform(tree, template)

        if message:
            return str(message)
        else:
            return s3xrc.xml.tostring(tree, pretty_print=True)


# -----------------------------------------------------------------------------
def shn_crud_strings(table_name,
                     table_name_plural = None):

    """ Creates the strings for the title of/in the various CRUD Forms.

        @author: Michael Howden (michael@aidiq.com)

        @note: Whilst this is useful for RAD purposes, it isn't ideal for
               maintenance of translations, so it's use should be discouraged
               for the core system

        @arguments:
            table_name - string - The User's name for the resource in the table - eg. "Person"
            table_name_plural - string - The User's name for the plural of the resource in the table - eg. "People"

        @returns:
            class "gluon.storage.Storage" (Web2Py)

        @example
            s3.crud_strings[<table_name>] = shn_crud_strings(<table_name>, <table_name_plural>)

    """

    if not table_name_plural:
        table_name_plural = table_name + "s"

    ADD = T("Add") + " " + T(table_name)
    LIST = T("List") + " " + T(table_name_plural)

    table_strings = Storage(
        title = T(table_name),
        title_plural = T(table_name_plural),
        title_create = ADD,
        title_display = T(table_name) + " " + T("Details"),
        title_list = LIST,
        title_update = T("Edit") + " " + T(table_name),
        title_search = T("Search") + " " + T(table_name_plural),
        subtitle_create = T("Add New") + " " + T(table_name),
        subtitle_list = T(table_name_plural),
        label_list_button = LIST,
        label_create_button = ADD,
        label_delete_button = T("Delete") + " " + T(table_name),
        msg_record_created =  T(table_name) + " " + T("added"),
        msg_record_modified =  T(table_name) + " " + T("updated"),
        msg_record_deleted = T(table_name) + " " + T("deleted"),
        msg_list_empty = T("No") + " " + T(table_name_plural) + " " + T("currently registered")
    )

    return table_strings


# -----------------------------------------------------------------------------
def shn_get_crud_string(tablename, name):

    """ Get the CRUD strings for a table """

    crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
    not_found = s3.crud_strings.get(name, None)

    return crud_strings.get(name, not_found)


# -----------------------------------------------------------------------------
def shn_import_table(table_name,
                     import_if_not_empty = False):

    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            If a table is empty, it will import values into that table from:
            /private/import/tables/<table>.csv.

        @arguments:
            table_name - string - The name of the table
            import_if_not_empty - bool

    """

    table = db[table_name]
    if not db(table.id > 0).count() or import_if_not_empty:
        import_file = os.path.join(request.folder,
                                   "private", "import", "tables",
                                   table_name + ".csv")
        table.import_from_csv_file(open(import_file,"r"))


# -----------------------------------------------------------------------------
def shn_last_update(table, record_id):

    """ @todo: docstring?? """

    if table and record_id:
        record = table[record_id]
        if record:
            mod_on_str  = T(" on ")
            mod_by_str  = T(" by ")

            modified_on = ""
            if "modified_on" in table.fields:
                modified_on = "%s%s" % (mod_on_str, shn_as_local_time(record.modified_on))

            modified_by = ""
            if "modified_by" in table.fields:
                user = auth.settings.table_user[record.modified_by]
                if user:
                    person = db(db.pr_person.uuid == user.person_uuid).select(limitby=(0, 1)).first()
                    if person:
                        modified_by = "%s%s" % (mod_by_str, vita.fullname(person))

            if len(modified_on) or len(modified_by):
                last_update = "%s%s%s" % (T("Record last updated"), modified_on, modified_by)
                return last_update
    return None


# -----------------------------------------------------------------------------
def shn_represent_file(file_name,
                       table,
                       field = "file"):

    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            Represents a file (stored in a table) as the filename with a link to that file
            THIS FUNCTION IS REDUNDANT AND CAN PROBABLY BE REPLACED BY shn_file_represent in models/06_doc.py

    """

    import base64
    url_file = crud.settings.download_url + "/" + file_name

    if db[table][field].uploadfolder:
        path = db[table][field].uploadfolder
    else:
        path = os.path.join(db[table][field]._db._folder, "..", "uploads")
    pathfilename = os.path.join(path, file_name)

    try:
        #f = open(pathfilename,"r")
        #filename = f.filename
        regex_content = re.compile("([\w\-]+\.){3}(?P<name>\w+)\.\w+$")
        regex_cleanup_fn = re.compile('[\'"\s;]+')

        m = regex_content.match(file_name)
        filename = base64.b16decode(m.group("name"), True)
        filename = regex_cleanup_fn.sub("_", filename)
    except:
        filename = file_name

    return A(filename, _href = url_file)


# -----------------------------------------------------------------------------
def s3_represent_multiref(table, opt, represent=None):

    """ @todo: docstring?? """

    if represent is None:
        if "name" in table.fields:
            represent = lambda r: r and r.name or UNKNOWN_OPT

    if isinstance(opt, (int, long, str)):
        query = (table.id == opt)
    else:
        query = (table.id.belongs(opt))
    if "deleted" in table.fields:
        query = query & (table.deleted == False)

    records = db(query).select()
    try:
        options = [represent(r) for r in records]
    except TypeError:
        options = [represent % r for r in records]

    if options:
        return ", ".join(options)
    else:
        return UNKNOWN_OPT


# -----------------------------------------------------------------------------
def shn_table_links(reference):

    """ Return a dict of tables & their fields which have references to the
        specified table

        @deprecated: to be replaced by db[tablename]._referenced_by

    """

    tables = {}
    for table in db.tables:
        count = 0
        for field in db[table].fields:
            if db[table][field].type == "reference %s" % reference:
                if count == 0:
                    tables[table] = {}
                tables[table][count] = field
                count += 1

    return tables


# -----------------------------------------------------------------------------
def shn_rheader_tabs(r, tabs=[], paging=False):

    """ Constructs a DIV of component links for a S3RESTRequest

        @param tabs: the tabs as list of tuples (title, component_name, vars),
            where vars is optional
        @param paging: add paging buttons previous/next to the tabs

    """

    rheader_tabs = []

    tablist = []
    previous = next = None

    for i in xrange(len(tabs)):
        title, component = tabs[i][:2]
        if len(tabs[i]) > 2:
            _vars = tabs[i][2]
        else:
            _vars = r.request.vars

        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
            if not component:
                component = None
        else:
            function = r.request.function

        if i == len(tabs)-1:
            tab = Storage(title=title, _class = "rheader_tab_last")
        else:
            tab = Storage(title=title, _class = "rheader_tab_other")
        if i > 0 and tablist[i-1]._class == "rheader_tab_here":
            next = tab

        if component:
            if r.component and r.component.name == component or \
               r.custom_action and r.method == component:
                tab.update(_class = "rheader_tab_here")
                previous = i and tablist[i-1] or None
            args = [r.id, component]
            tab.update(_href=URL(r=request, f=function, args=args, vars=_vars))
        else:
            if not r.component:
                tab.update(_class = "rheader_tab_here")
                previous = i and tablist[i-1] or None
            args = [r.id]
            vars = Storage(_vars)
            if not vars.get("_next", None):
                vars.update(_next=URL(r=request, f=function, args=args, vars=_vars))
            tab.update(_href=URL(r=request, f=function, args=args, vars=vars))

        tablist.append(tab)
        rheader_tabs.append(SPAN(A(tab.title, _href=tab._href), _class=tab._class))

    if rheader_tabs:
        if paging:
            if next:
                rheader_tabs.insert(0, SPAN(A(">", _href=next._href), _class="rheader_next_active"))
            else:
                rheader_tabs.insert(0, SPAN(">", _class="rheader_next_inactive"))
            if previous:
                rheader_tabs.insert(0, SPAN(A("<", _href=previous._href), _class="rheader_prev_active"))
            else:
                rheader_tabs.insert(0, SPAN("<", _class="rheader_prev_inactive"))
        rheader_tabs = DIV(rheader_tabs, _id="rheader_tabs")
    else:
        rheader_tabs = ""

    return rheader_tabs

# -----------------------------------------------------------------------------
def shn_import_csv(file, table=None):

    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()

#
# shn_custom_view -------------------------------------------------------------
#
def shn_custom_view(r, default_name, format=None):

    """ Check for custom view """

    prefix = r.request.controller

    if r.component:

        custom_view = "%s_%s_%s" % (r.name, r.component_name, default_name)

        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

        if not os.path.exists(_custom_view):
            custom_view = "%s_%s" % (r.name, default_name)
            _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    else:
        if format:
            custom_view = "%s_%s_%s" % (r.name, default_name, format)
        else:
            custom_view = "%s_%s" % (r.name, default_name)
        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    if os.path.exists(_custom_view):
        response.view = "%s/%s" % (prefix, custom_view)
    else:
        if format:
            response.view = default_name.replace(".html", "_%s.html" % format)
        else:
            response.view = default_name


# -----------------------------------------------------------------------------
def shn_copy(r, **attr):

    """ Copy a record

        used as REST method handler for S3Resources

        @todo: move into S3CRUDHandler

    """

    redirect(URL(r=request, args="create", vars={"from_record":r.id}))


# -----------------------------------------------------------------------------
def shn_list_item(table, resource, action, main="name", extra=None):

    """ Display nice names with clickable links & optional extra info

        used in shn_search

    """

    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[table.id, action])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)


# -----------------------------------------------------------------------------
def shn_represent_extra(table, module, resource, deletable=True, extra=None):

    """ Display more than one extra field (separated by spaces)

        used in shn_search

    """

    authorised = shn_has_permission("delete", table._tablename)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % \
                             (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % \
                         (resource, table.id))
    return ",".join( item_list )


# -----------------------------------------------------------------------------
def shn_represent(table, module, resource, deletable=True, main="name", extra=None):

    """ Designed to be called via table.represent to make t2.search() output useful

        used in shn_search

    """

    db[table].represent = lambda table: \
                          shn_list_item(table, resource,
                                        action="display",
                                        main=main,
                                        extra=shn_represent_extra(table,
                                                                  module,
                                                                  resource,
                                                                  deletable,
                                                                  extra))
    return


# -----------------------------------------------------------------------------
def shn_search(r, **attr):

    """ Search function, mostly used with the JSON representation

        used as method handler for S3Resources

        @todo: replace by a S3MethodHandler

    """

    deletable = attr.get("deletable", True)
    main = attr.get("main", None)
    extra = attr.get("extra", None)

    request = r.request

    # Filter Search list to just those records which user can read
    query = shn_accessible_query("read", r.table)

    # Filter search to items which aren't deleted
    if "deleted" in r.table:
        query = (r.table.deleted == False) & query

    # Respect response.s3.filter
    if response.s3.filter:
        query = response.s3.filter & query

    if r.representation in shn_interactive_view_formats:

        shn_represent(r.table, r.prefix, r.name, deletable, main, extra)
        search = t2.search(r.table, query=query)
        #search = crud.search(r.table, query=query)[0]

        # Check for presence of Custom View
        shn_custom_view(r, "search.html")

        # CRUD Strings
        title = s3.crud_strings.title_search

        output = dict(search=search, title=title)

    elif r.representation == "json":

        _vars = request.vars
        _table = r.table

        # JQuery Autocomplete uses "q" instead of "value"
        value = _vars.value or _vars.q or None

        if _vars.field and _vars.filter and value:
            field = str.lower(_vars.field)
            _field = _table[field]

            # Optional fields
            if "field2" in _vars:
                field2 = str.lower(_vars.field2)
            else:
                field2 = None
            if "field3" in _vars:
                field3 = str.lower(_vars.field3)
            else:
                field3 = None
            if "parent" in _vars and _vars.parent:
                if _vars.parent == "null":
                    parent = None
                else:
                    parent = int(_vars.parent)
            else:
                parent = None
            if "exclude_field" in _vars:
                exclude_field = str.lower(_vars.exclude_field)
                if "exclude_value" in _vars:
                    exclude_value = str.lower(_vars.exclude_value)
                else:
                    exclude_value = None
            else:
                exclude_field = None
                exclude_value = None

            limit = int(_vars.limit or 0)

            filter = _vars.filter
            if filter == "~":
                if field2 and field3:
                    # pr_person name search
                    if " " in value:
                        value1, value2 = value.split(" ", 1)
                        query = query & ((_field.like("%" + value1 + "%")) & \
                                        (_table[field2].like("%" + value2 + "%")) | \
                                        (_table[field3].like("%" + value2 + "%")))
                    else:
                        query = query & ((_field.like("%" + value + "%")) | \
                                        (_table[field2].like("%" + value + "%")) | \
                                        (_table[field3].like("%" + value + "%")))

                elif exclude_field and exclude_value:
                    # gis_location hierarchical search
                    # Filter out poor-quality data, such as from Ushahidi
                    query = query & (_field.like("%" + value + "%")) & \
                                    (_table[exclude_field] != exclude_value)

                elif parent:
                    # gis_location hierarchical search
                    # NB Currently not used - we allow people to search freely across all the hierarchy
                    # SQL Filter is immediate children only so need slow lookup
                    #query = query & (_table.parent == parent) & \
                    #                (_field.like("%" + value + "%"))
                    children = gis.get_children(parent)
                    children = children.find(lambda row: value in str.lower(row.name))
                    item = children.json()
                    query = None

                else:
                    # Normal single-field
                    query = query & (_field.like("%" + value + "%"))

                if query:
                    if limit:
                        item = db(query).select(limitby=(0, limit)).json()
                    else:
                        item = db(query).select().json()

            elif filter == "=":
                query = query & (_field == value)
                if parent:
                    # e.g. gis_location hierarchical search
                    query = query & (_table.parent == parent)

                if _table == db.gis_location:
                    # Don't return unnecessary fields (WKT is large!)
                    item = db(query).select(_table.id, _table.uuid, _table.parent, _table.name, _table.level, _table.lat, _table.lon, _table.addr_street).json()
                else:
                    item = db(query).select().json()

            elif filter == "<":
                query = query & (_field < value)
                item = db(query).select().json()

            elif filter == ">":
                query = query & (_field > value)
                item = db(query).select().json()

            else:
                item = s3xrc.xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                raise HTTP(400, body=item)

        else:
            #item = s3xrc.xml.json_message(False, 400, "Search requires specifying Field, Filter & Value!")
            #raise HTTP(400, body=item)
            # Provide a simplified JSON output which is in the same format as the Search one
            # (easier to parse than S3XRC & means no need for different parser for filtered/unfiltered)
            if _table == db.gis_location:
                # Don't return unnecessary fields (WKT is large!)
                item = db(query).select(_table.id, _table.name, _table.level).json()
            else:
                item = db(query).select().json()

        response.view = "xml.html"
        output = dict(item=item)

    else:
        raise HTTP(501, body=BADFORMAT)

    return output


# -----------------------------------------------------------------------------
def shn_barchart (r, **attr):

    """ Provide simple barcharts for resource attributes
        SVG representation uses the SaVaGe library
        Need to request a specific value to graph in request.vars

        used as REST method handler for S3Resources

        @todo: replace by a S3MethodHandler

    """

    import gluon.contrib.simplejson as json

    # Get all the variables and format them if needed
    valKey = r.request.vars.get("value")

    nameKey = r.request.vars.get("name")
    if not nameKey and r.table.get("name"):
        # Try defaulting to the most-commonly used:
        nameKey = "name"

    # The parameter value is required; it must be provided
    # The parameter name is optional; it is useful, but we don't need it
    # Here we check to make sure we can find value in the table,
    # and name (if it was provided)
    if not r.table.get(valKey):
        raise HTTP (400, s3xrc.xml.json_message(success=False, status_code="400", message="Need a Value for the Y axis"))
    elif nameKey and not r.table.get(nameKey):
        raise HTTP (400, s3xrc.xml.json_message(success=False, status_code="400", message=nameKey + " attribute not found in this resource."))

    start = request.vars.get("start")
    if start:
        start = int(start)

    limit = r.request.vars.get("limit")
    if limit:
        limit = int(limit)

    settings = r.request.vars.get("settings")
    if settings:
        settings = json.loads(settings)
    else:
        settings = {}

    if r.representation.lower() == "svg":
        r.response.headers["Content-Type"] = "image/svg+xml"

        graph = local_import("savage.graph")
        bar = graph.BarGraph(settings=settings)

        title = deployment_settings.modules.get(module).name_nice
        bar.setTitle(title)

        if nameKey:
            xlabel = r.table.get(nameKey).label
            if xlabel:
                bar.setXLabel(str(xlabel))
            else:
                bar.setXLabel(nameKey)

        ylabel = r.table.get(valKey).label
        if ylabel:
            bar.setYLabel(str(ylabel))
        else:
            bar.setYLabel(valKey)

        try:
            records = r.resource.load(start, limit)
            for entry in r.resource:
                val = entry[valKey]

                # Can't graph None type
                if not val is None:
                    if nameKey:
                        name = entry[nameKey]
                    else:
                        name = None
                    bar.addBar(name, val)
            return bar.save()
        # If the field that was provided was not numeric, we have problems
        except ValueError:
            raise HTTP(400, "Bad Request")
    else:
        raise HTTP(501, body=BADFORMAT)


# -----------------------------------------------------------------------------
def s3_rest_controller(prefix, resourcename, **attr):

    """ Helper function to apply the S3Resource REST interface (new version)

        @param prefix: the application prefix
        @param resourcename: the resource name (without prefix)
        @param attr: additional keyword parameters

        Any keyword parameters will be copied into the output dict (provided
        that the output is a dict). If a keyword parameter is callable, then
        it will be invoked, and its return value will be added to the output
        dict instead. The callable receives the S3Request as its first and
        only parameter.

        CRUD can be configured per table using:

            s3xrc.model.configure(table, **attr)

        *** Redirection:

        create_next             URL to redirect to after a record has been created
        update_next             URL to redirect to after a record has been updated
        delete_next             URL to redirect to after a record has been deleted

        *** Form configuration:

        list_fields             list of names of fields to include into list views
        subheadings             Sub-headings (see separate documentation)
        listadd                 Enable/Disable add-form in list views

        *** CRUD configuration:

        editable                Allow/Deny record updates in this table
        deletable               Allow/Deny record deletions in this table
        insertable              Allow/Deny record insertions into this table
        copyable                Allow/Deny record copying within this table

        *** Callbacks:

        create_onvalidation     Function/Lambda for additional record validation on create
        create_onaccept         Function/Lambda after successful record insertion

        update_onvalidation     Function/Lambda for additional record validation on update
        update_onaccept         Function/Lambda after successful record update

        onvalidation            Fallback for both create_onvalidation and update_onvalidation
        onaccept                Fallback for both create_onaccept and update_onaccept
        ondelete                Function/Lambda after record deletion

    """

    # Set method handlers
    s3xrc.set_handler("search", shn_search)
    s3xrc.set_handler("copy", shn_copy)
    s3xrc.set_handler("barchart", shn_barchart)

    # Parse and execute the request
    resource, r = s3xrc.parse_request(prefix, resourcename)
    output = resource.execute_request(r, **attr)

    # Add default action buttons in list views
    if isinstance(output, dict) and not r.method or r.method=="search_simple":

        if response.s3.actions is None:

            prefix, name, table, tablename = r.target()
            authorised = shn_has_permission("update", tablename)

            # If the component has components itself, then use the
            # component's native controller for CRU(D) => make sure
            # you have one, or override by native=False
            if r.component and s3xrc.model.has_components(prefix, name):
                native = output.get("native", True)
            else:
                native = False

            # Get table config
            model = s3xrc.model
            listadd = model.get_config(table, "listadd", True)
            editable = model.get_config(table, "editable", True)
            deletable = model.get_config(table, "deletable", True)
            copyable = model.get_config(table, "copyable", False)

            # URL to open the resource
            open_url = r.resource.crud._linkto(r,
                                               authorised=authorised,
                                               update=editable,
                                               native=native)("[id]")

            # Add action buttons for Open/Delete/Copy as appropriate
            shn_action_buttons(r,
                               deletable=deletable,
                               copyable=copyable,
                               read_url=open_url,
                               update_url=open_url)

            # Override Add-button, link to native controller and put
            # the primary key into vars for automatic linking
            if native and not listadd and \
               shn_has_permission("create", tablename):
                label = shn_get_crud_string(tablename,
                                            "label_create_button")
                hook = r.resource.components[name]
                fkey = "%s.%s" % (name, hook.fkey)
                vars = request.vars.copy()
                vars.update({fkey: r.id})
                url = str(URL(r=request, c=prefix, f=name,
                              args=["create"], vars=vars))
                add_btn = A(label, _href=url, _class="action-btn")
                output.update(add_btn=add_btn)

    return output

# END
# *****************************************************************************
