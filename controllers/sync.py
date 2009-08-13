﻿# -*- coding: utf-8 -*-

module = 'admin'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
# - can Insert/Delete items from default menus within a function, if required.
response.menu_options = admin_menu_options

# Web2Py Tools functions
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # Sync webservices don't use sessions, so avoid cluttering up the storage
    session.forget()
    return service()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

logtable = "sync_log"
    
@auth.requires_membership('Administrator')
def partner():
    "RESTlike CRUD controller"
    db.sync_partner.uuid.label = 'UUID'
    #db.sync_partner.password.readable = False
    title_create = T('Add Partner')
    title_display = T('Partner Details')
    title_list = T('List Partners')
    title_update = T('Edit Partner')
    title_search = T('Search Partners')
    subtitle_create = T('Add New Partner')
    subtitle_list = T('Partners')
    label_list_button = T('List Partners')
    label_create_button = T('Add Partner')
    label_search_button = T('Search Partners')
    msg_record_created = T('Partner added')
    msg_record_modified = T('Partner updated')
    msg_record_deleted = T('Partner deleted')
    msg_list_empty = T('No Partners currently registered')
    s3.crud_strings.sync_partner = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    return shn_rest_controller('sync', 'partner')

@auth.requires_membership('Administrator')
def setting():
    "RESTlike CRUD controller"
    db.sync_setting.uuid.writable = False
    db.sync_setting.uuid.label = 'UUID'
    db.sync_setting.uuid.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("UUID|The unique identifier which identifies this server to other instances."))
    db.sync_setting.policy.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Policy|The default Sync Policy for new Partners."))
    db.sync_setting.username.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Username|The default Username used to login to new Partners."))
    db.sync_setting.password.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Password|The default Password used to login to new Partners."))
    db.sync_setting.rpc_service_url.writable = False
    db.sync_setting.rpc_service_url.label = T('RPC Service URL')
    title_update = T('Edit Sync Settings')
    label_list_button = None
    msg_record_modified = T('Sync Settings updated')
    s3.crud_strings.sync_setting = Storage(title_update=title_update,label_list_button=label_list_button,msg_record_modified=msg_record_modified)
    crud.settings.update_next = URL(r=request, args=['update', 1])
    return shn_rest_controller('sync', 'setting', deletable=False, listadd=False)

@auth.requires_login()
def history():
    "Shows history of database synchronizations"
    title = T('Automatic Database Synchronization History')
    #http://groups.google.com/group/web2py/browse_thread/thread/cc6180d335b14d62/c78affba95fcd4b5?lnk=gst&q=database+selection+unique#c78affba95fcd4b5
    #there is no good way of avoiding this, we can't restrict 'distinct' to fewer attributes
    history = db().select(db[logtable].ALL, orderby=db[logtable].timestamp)
    functions = ['getdata', 'putdata'] #as of two, only two funtions require for true syncing
    synced = {}
    for i in history:
        synced[i.uuid + i.function] = i
    todel = [i for i, j in synced.iteritems() if not ( j.uuid + functions[0] in synced.keys() and j.uuid + functions[1] in synced.keys() )]
    for each in todel:
        del synced[each]
    synced = synced.values()
    syncedids = [i.id for i in synced]
    # Sort by time
    timestamps = [i.timestamp for i in synced]

    # insertion_sort
    for i in range(1, len(timestamps)):
        save = timestamps[i]
        saverow = synced[i]
        j = i
        while j > 0 and timestamps[j - 1] > save:
            timestamps[j] = timestamps[j - 1]
            synced[j] = synced[j-1]
            j -= 1
        timestamps[j] = save
        synced[j] = saverow
    synced.reverse()
    
    # SQLRows to list so that we can reverse it
    history = [i for i in history]
    history.reverse()
    return dict(title=title, synced=synced, syncedids=syncedids, history=history)

@service.json
@service.xml
@service.jsonrpc
@service.xmlrpc
def getconf():
    """
    Returns configurations of the system.
    Used by local DaemonX
    """
    if not request.client == "127.0.0.1":
        # Only accept calls from localhost
        return
    temp = db().select(db.sync_setting.ALL)[0]
    toreturn = {}
    for i in temp:
        if not i is "update_record":
            toreturn[str(i)] = temp[str(i)]
    return toreturn
    
@service.json
@service.xml
@service.jsonrpc
@service.xmlrpc
def getAuthCred(uuid):
    """
    Returns configurations of the system.
    Used by local DaemonX
    """
    if not request.client == "127.0.0.1":
        return
    temp = db(db.sync_partner.uuid == uuid).select()
    toreturn = {}
    if len(temp) is 0:
        toreturn['username'] = "username"
        toreturn['password'] = "password"
    else:
        toreturn['username'] = temp[0].username
        toreturn['password'] = temp[0].password
    return toreturn

@service.json
@service.xml
@service.jsonrpc
@service.xmlrpc
def putdata(uuid, username, password, nicedbdump):
    """
    Import data using webservices
    uuid is that of the calling system
    username/password must be valid in our local auth_user table
    nicedbdump is a properly-formatted data dump
    """
    # 1st determine if the UUID is valid
    sync_partners = db().select(db.sync_partner.uuid)
    for partner in sync_partners:
        if uuid == partner[0].uuid:
            sync_policy = db(db.sync_setting.uuid==uuid).select()[0].policy
            # no need to carry on looping
            break
    if not sync_policy:
        return T("Invalid UUID!")
    
    if sync_policy == 1:
        # No Sync
        return T("No sync permitted!")
    
    # Authentication is mandatory here
    user = auth.login_bare(username, password)
    if not user:
        return T("Authentication failed!")
    
    # Parsing nicedbdump to see if it valid, otherwise we will throw error    
    # validator: validates if nicedbdump adhears to protocol defined by us
    # we never check nicedbdump size because its size reflects number of tables to be synced, as sahana is developing fastly so syncable tables can increase, moreover it doesnt fixin sync protocol
    if type(nicedbdump) == list:
        for nicetabledump in nicedbdump:
            if type(nicetabledump) == list:
                if len(nicetabledump) == 3:
                    # we have the right number of options & can proceed
                    table, table_attributes, table_data = nicetabledump[0], nicetabledump[1], nicetabledump[2]
                    # This gives the same result as above:
                    #table, table_attributes, table_data = nicetabledump
                    if (type(table) == str or type(table) == unicode) and type(table_attributes) == list and type(table_data) == list:
                        for attrib in table_attributes:
                            if not (type(attrib) == str or type(attrib) == unicode):
                                return 'at least one attribute name is not of string type'
                        if not 'uuid' in table_attributes:
                            return 'at least one table doesnt have "uuid" as attribute'
                        if not 'modified_on' in table_attributes:
                            return 'at least one table doesnt have "modified_on" attribute'
                        if not 'id' in table_attributes:
                            return 'at least one table doesnt have "id" attribute'
                        size = 0
                        isfirstiter = True
                        for row in table_data:
                            if type(row) == list:
                                if isfirstiter == True:
                                    size = len(row)
                                    isfirstiter = False
                                if not size == len(row):
                                    return 'all rows in ' + table + ' dont have same length'
                            else:
                                return 'row type can only be a list, at least one element in ' + table + ' isnt of list type'
                        if not((size == 0) or (size == len(table_attributes))):
                            return 'you havent stated exact number of attribute names as attributes present in ' + table
                    else:
                        #return str(type(table)), str(type(table_attributes)), str(type(table_data))
                        return 'first element is each table is name of table(string), second is attribute names(list), third is data(list of list), atleast one of them in ' + table + ' is not of accepted data type'
                else:
                    return 'each table must have three elements, you havent passed three'
            else:
                return 'each table is a list, you havent passed atleast one table as list'
    else:
        return 'data can only in form of list'

    # Now data object is validated, lets put it in object
    for table in nicedbdump:
        tablename = str(table[0]) #it might be unicode here
        tableattrib = table[1]
        tablerows = table[2]
            
        if tablename in db:
            # If a table in sent data is not present in the local database, it is simply ignored
            canupdate = shn_has_permission('update', tablename)
            caninsert = shn_has_permission('insert', tablename)
            if not (canupdate or caninsert):
                #build error return if required
                continue
            indexesavailable = []
            for anattrib in tableattrib:
                if anattrib in db[tablename]["fields"]:
                    indexesavailable.append(tableattrib.index(anattrib))
            for row in tablerows:
                rowuuid = row[tableattrib.index('uuid')]
                query = (db[tablename]['uuid'] == rowuuid)
                uuidcount = db(query).count()
                vals = {}
                for eachattribindex in indexesavailable:
                    vals[tableattrib[eachattribindex]] = row[eachattribindex]
                # ids are assigned by web2py itself
                if 'id' in vals:
                    del vals['id']
                # vals now has dictionary ready for insert/update
                
                if uuidcount == 0 and caninsert:
                    # This row isn't present in current database
                    rowid = db[tablename].insert(**vals)
                    shn_audit_noform(resource = tablename, record = rowid, operation='create', representation='json')
                elif uuidcount == 1 and canupdate:
                    # We have a Duplicate record, so need to know which record to use, according to policy
                    if sync_policy == 2:
                        # Newer Timestamp: Update only if given row is newer
                        a = row[tableattrib.index('modified_on')]
                        a = datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
                        b = db(db[tablename].uuid == row[tableattrib.index('uuid')]).select(db[tablename].modified_on)                
                        b = b[0].modified_on
                        if a > b:
                            rowid = db(query).update(**vals)
                            shn_audit_noform(resource = tablename, record = rowid, operation='update', representation='json')
                    elif sync_policy == 4:
                        # Replace All
                        rowid = db(query).update(**vals)
                        shn_audit_noform(resource = tablename, record = rowid, operation='update', representation='json')
                else:
                    #uuidcount can never be more than 2, if we reach this place it means user is restricted by authentication
                    #if interpreter reached this line then either I am bad coder or you are hacker
                    return "error code number ..."
    
    # Logging (not auditing)
    db[logtable].insert(
        uuid=uuid,
        function='putdata',
        timestamp=request.utcnow,
        )
    
    return True

#function will take a date and uuid to caller and return new data only
#service.json traslates SQL into json but json-rpc doesnt, so we convert it into lists
@service.json
@service.xml
@service.jsonrpc
@service.xmlrpc
def getdata(uuid, username, password, timestamp = None):
    """
    Export data using webservices
    This function will never be called by foreign service, so it doesn't require authentication, but for the sake of API, we add this facility
    http://localhost:8000/sahana/sync/call/json/getdata?timestamp=0&uuid=myuuid&username=user@domain.com&password=mypassword
    If no timestamp is passed, system will return new data since the last sync operation
    """
    
    if not IS_DATETIME(timestamp):
        return "invalid call -- time?"

    # Authentication using username and password unless on localhost
    if not request.client == "127.0.0.1":
        user = auth.login_bare(username, password)
        if not user:
            return "authentication failed"
    
    #this is buggy, check it
    #timestamp determination
    if timestamp == None:
        lastsynctime = db(db[logtable].uuid == uuid).select(db[logtable].timestamp, orderby=~db[logtable].id)
        if len(lastsynctime) == 0:
            # There is no sync operation with this uuid
            # so return everything
            timestamp = 0
        else:
            # The date since last sync
            timestamp = lastsynctime[0] 

    tables = [['budget', 'item'],
            ['budget', 'kit'],
            ['or', 'organisation'],
            ['or', 'office'],
            ['pr', 'person'],
            ['cr', 'shelter'],
            ['gis', 'feature'],
            ['gis', 'location']]

    nicedbdump = []
    for module, resource in tables:
        _table = '%s_%s' % (module, resource)
        table = db[_table]
        query = shn_accessible_query('read', table)
        query = query & (db[_table].modified_on > timestamp)
        sqltabledump = db(query).select(db[_table].ALL) 
        nicetabledump = []
        nicetabledump.append(_table)
        nicetabledump.append(db[_table]["fields"])
        nicetabledumpdata = []
        for row in sqltabledump:
            temp = [row[col] for col in db[_table]["fields"]]
            nicetabledumpdata.append(temp)
        shn_audit_read(operation = 'read', resource = _table, record=None, representation= 'json')
        nicetabledump.append(nicetabledumpdata)
        #nicetabledump.append(function(table, query)) # we aren't using this function because then we will have to manually translate json back into objects, let web2py do it for us
        nicedbdump.append(nicetabledump)
    
    # Logging (not auditing)
    db[logtable].insert(
        uuid=uuid,
        function='getdata',
        timestamp=request.utcnow,
        )
    
    return nicedbdump