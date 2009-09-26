# -*- coding: utf-8 -*-

module = 'admin'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
# - can Insert/Delete items from default menus within a function, if required.
response.menu_options = admin_menu_options

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@auth.requires_membership('Administrator')
def setting():
    "RESTlike CRUD controller"
    s3.crud_strings.setting.title_update = T('Edit Settings')
    s3.crud_strings.setting.msg_record_modified = T('Settings updated')
    s3.crud_strings.setting.label_list_button = None
    #crud.settings.update_next = URL(r=request, args=['update', 1])
    return shn_rest_controller('s3', 'setting', deletable=False, listadd=False, onvalidation=lambda form: theme_check(form), onaccept=lambda form: theme_apply(form))

@auth.requires_membership('Administrator')
def theme():
    "RESTlike CRUD controller"
    return shn_rest_controller('admin', 'theme', list_fields=['id', 'name', 'logo', 'footer', 'col_background'], onvalidation=lambda form: theme_check(form))

def theme_apply(form):
    "Apply the Theme specified by Form"
    if form.vars.theme:
        # Valid form
        # Relevant paths
        template = os.path.join(request.folder, 'static', 'styles', 'S3', 'template.css')
        tmp_folder = os.path.join(request.folder, 'static', 'scripts', 'tools')
        out_file = os.path.join(request.folder, 'static', 'styles', 'S3', 'sahana.css')
        out_file2 = os.path.join(request.folder, 'static', 'styles', 'S3', 'sahana.min.css')
        # Check permissions
        if not os.access(template, os.R_OK):
            session.error = T('Template file %s not readable - unable to apply theme!' % template)
            redirect(URL(r=request, args=request.args))
        if not os.access(tmp_folder, os.W_OK):
            session.error = T('Temp folder %s not writable - unable to apply theme!' % tmp_folder)
            redirect(URL(r=request, args=request.args))
        if not os.access(out_file, os.W_OK):
            session.error = T('CSS file %s not writable - unable to apply theme!' % out_file)
            redirect(URL(r=request, args=request.args))
        if not os.access(out_file2, os.W_OK):
            session.error = T('CSS file %s not writable - unable to apply theme!' % out_file2)
            redirect(URL(r=request, args=request.args))
        # Read in Template
        inpfile = open(template, 'r')
        lines = inpfile.readlines()
        inpfile.close()
        # Read settings from Database
        theme = db(db.admin_theme.id == form.vars.theme).select()[0]
        logo = theme.logo
        # Write out CSS
        ofile = open(out_file, 'w')
        for line in lines:
            line = line.replace("YOURLOGOHERE", logo)
            # Iterate through Colours
            for key in theme.keys():
                if key[:4] == 'col_':
                    line = line.replace(key, theme[key])
            ofile.write(line)
        ofile.close()

        # Minify
        from subprocess import PIPE, check_call
        currentdir = os.getcwd()
        os.chdir(os.path.join(currentdir, request.folder, 'static', 'scripts', 'tools'))
        import sys
        # If started as a services os.sys.executable is no longer python on
        # windows.
        if ("win" in sys.platform):
            pythonpath = os.path.join(sys.prefix, 'python.exe')
        else:
            pythonpath = os.sys.executable
        try:
            proc = check_call([pythonpath, 'build.sahana.py', 'CSS', 'NOGIS'], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        except:
            session.error = T('Error encountered while applying the theme.')
            redirect(URL(r=request, args=request.args))
        os.chdir(currentdir)

        # Don't do standard redirect to List view as we only want this option available
        redirect(URL(r=request, args=['update', 1]))
    else:
        session.error = INVALIDREQUEST
        redirect(URL(r=request))

def theme_check(form):
    "Check the Theme has valid files available"
    # Check which form we're called by
    if form.vars.theme:
        # Called from Settings
        theme = db(db.admin_theme.id == form.vars.theme).select()[0]
        logo = theme.logo
        footer = theme.footer
    elif form.vars.logo and form.vars.footer:
        # Called from Theme
        logo = form.vars.logo
        footer = form.vars.footer
    else:
        session.error = INVALIDREQUEST
        redirect(URL(r=request))
    _logo = os.path.join(request.folder, 'static', logo)
    _footer = os.path.join(request.folder, 'views', footer)
    if not os.access(_logo, os.R_OK):
        session.error = T('Logo file %s missing!' % logo)
        redirect(URL(r=request, args=request.args))
    if not os.access(_footer, os.R_OK):
        session.error = T('Footer file %s missing!' % footer)
        redirect(URL(r=request, args=request.args))
    # Validation passed
    return
    
@auth.requires_membership('Administrator')
def user():
    "RESTlike CRUD controller"
    # Add users to Person Registry & 'Authenticated' role
    crud.settings.create_onaccept = lambda form: auth.shn_register(form)
    # Allow the ability for admin to Disable logins
    db.auth_user.registration_key.writable = True
    db.auth_user.registration_key.label = T('Disabled?')
    db.auth_user.registration_key.requires = IS_IN_SET(['','disabled'])
    return shn_rest_controller('auth', 'user', main='first_name')
    
@auth.requires_membership('Administrator')
def group():
    "RESTlike CRUD controller"
    return shn_rest_controller('auth', 'group', main='role')
    
# Unused as poor UI
@auth.requires_membership('Administrator')
def membership():
    "RESTlike CRUD controller"
    return shn_rest_controller('auth', 'membership', main='user_id')
    
@auth.requires_membership('Administrator')
def users():
    "List/amend which users are in a Group"
    if len(request.args) == 0:
        session.error = T("Need to specify a role!")
        redirect(URL(r=request, f='group'))
    group = request.args[0]
    table = db.auth_membership
    query = table.group_id==group
    title = str(T('Role')) + ': ' + db.auth_group[group].role
    description = db.auth_group[group].description
    # Start building the Return
    output = dict(module_name=module_name, title=title, description=description, group=group)

    if auth.settings.username:
        username = 'username'
    else:
        username = 'email'

    # Audit
    crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'membership', 'html')
    # Many<>Many selection (Deletable, no Quantity)
    item_list = []
    sqlrows = db(query).select()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.user_id
        item_first = db.auth_user[id].first_name
        item_second = db.auth_user[id].last_name
        item_description = db.auth_user[id][username]
        id_link = A(id, _href=URL(r=request, f='user', args=['read', id]))
        checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
        item_list.append(TR(TD(id_link), TD(item_first), TD(item_second), TD(item_description), TD(checkbox), _class=theclass))
        
    if auth.settings.username:
        username_label = T('Username')
    else:
        username_label = T('Email')
    table_header = THEAD(TR(TH('ID'), TH(T('First Name')), TH(T('Last Name')), TH(username_label), TH(T('Remove'))))
    table_footer = TFOOT(TR(TD(_colspan=4), TD(INPUT(_id='submit_delete_button', _type='submit', _value=T('Remove')))))
    items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='group_remove_users', args=[group])))
        
    subtitle = T("Users")
    crud.messages.submit_button = T('Add')
    crud.messages.record_created = T('Role Updated')
    form = crud.create(table, next=URL(r=request, args=[group]))
    addtitle = T("Add New User to Role")
    output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form))
    return output

@auth.requires_membership('Administrator')
def group_remove_users():
    "Remove users from a group"
    if len(request.args) == 0:
        session.error = T("Need to specify a group!")
        redirect(URL(r=request, f='group'))
    group = request.args[0]
    table = db.auth_membership
    for var in request.vars:
        user = var
        query = (table.group_id==group) & (table.user_id==user)
        db(query).delete()
    # Audit
    #crud.settings.update_onaccept = lambda form: shn_audit_update(form, 'membership', 'html')
    session.flash = T("Users removed")
    redirect(URL(r=request, f='users', args=[group]))

@auth.requires_membership('Administrator')
def groups():
    "List/amend which groups a User is in"
    if len(request.args) == 0:
        session.error = T("Need to specify a user!")
        redirect(URL(r=request, f='user'))
    user = request.args[0]
    table = db.auth_membership
    query = table.user_id==user
    title = db.auth_user[user].first_name + ' ' + db.auth_user[user].last_name
    description = db.auth_user[user][username]
    # Start building the Return
    output = dict(module_name=module_name, title=title, description=description, user=user)

    # Audit
    crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'membership', 'html')
    # Many<>Many selection (Deletable, no Quantity)
    item_list = []
    sqlrows = db(query).select()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.group_id
        item_first = db.auth_group[id].role
        item_description = db.auth_group[id].description
        id_link = A(id, _href=URL(r=request, f='group', args=['read', id]))
        checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
        item_list.append(TR(TD(id_link), TD(item_first), TD(item_description), TD(checkbox), _class=theclass))
        
    table_header = THEAD(TR(TH('ID'), TH(T('Role')), TH(T('Description')), TH(T('Remove'))))
    table_footer = TFOOT(TR(TD(_colspan=3), TD(INPUT(_id='submit_delete_button', _type='submit', _value=T('Remove')))))
    items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='user_remove_groups', args=[user])))
        
    subtitle = T("Roles")
    crud.messages.submit_button = T('Add')
    crud.messages.record_created = T('User Updated')
    form = crud.create(table, next=URL(r=request, args=[user]))
    addtitle = T("Add New Role to User")
    output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form))
    return output

@auth.requires_membership('Administrator')
def user_remove_groups():
    "Remove groups from a user"
    if len(request.args) == 0:
        session.error = T("Need to specify a user!")
        redirect(URL(r=request, f='user'))
    user = request.args[0]
    table = db.auth_membership
    for var in request.vars:
        group = var
        query = (table.group_id==group) & (table.user_id==user)
        db(query).delete()
    # Audit
    #crud.settings.update_onaccept = lambda form: shn_audit_update(form, 'membership', 'html')
    session.flash = T("Groups removed")
    redirect(URL(r=request, f='groups', args=[user]))

# Import Data
@auth.requires_membership('Administrator')
def import_data():
    "Import data via POST upload to CRUD controller."
    title = T('Import Data')
    return dict(module_name=module_name, title=title)

@auth.requires_membership('Administrator')
def import_csv():
    "Import CSV data via POST upload to Database."
    file = request.vars.multifile.file
    try:
        import_csv(file)
        session.flash = T('Data uploaded')
    except: 
        session.error = T('Unable to parse CSV file!')
    redirect(URL(r=request))

# Export Data
@auth.requires_login()
def export_data():
    "Export data via CRUD controller."
    title = T('Export Data')
    return dict(module_name=module_name, title=title)

@auth.requires_login()
def export_csv():
    "Export entire database as CSV"
    import StringIO
    output = StringIO.StringIO()
    
    db.export_to_csv_file(output)
    
    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.csv')
    filename = "%s_database.csv" % (request.env.server_name)
    response.headers['Content-disposition'] = "attachment; filename=%s" % filename
    return output.read()
    
# Functional Testing
def handleResults():
    """Process the POST data returned from Selenium TestRunner.
    The data is written out to 2 files.  The overall results are written to 
    date-time-browserName-metadata.txt as a list of key: value, one per line.  The 
    suiteTable and testTables are written to date-time-browserName-results.html.
    """
    
    if not request.vars.result:
        # No results
        return
    
    # Read in results
    result = request.vars.result
    totalTime = request.vars.totalTime
    numberOfSuccesses = request.vars.numTestPasses
    numberOfFailures = request.vars.numTestFailures
    numberOfCommandSuccesses = request.vars.numCommandPasses
    numberOfCommandFailures = request.vars.numCommandFailures
    numberOfCommandErrors = request.vars.numCommandErrors

    suiteTable = ''
    if request.vars.suite:
        suiteTable = request.vars.suite
    
    testTables = []
    testTableNum = 1
    while request.vars['testTable.%s' % testTableNum]:
        testTable = request.vars['testTable.%s' % testTableNum]
        testTables.append(testTable)
        testTableNum += 1
        try:
            request.vars['testTable.%s' % testTableNum]
            pass
        except:
            break
    
    # Unescape the HTML tables
    import urllib
    suiteTable = urllib.unquote(suiteTable)
    testTables = map(urllib.unquote, testTables)

    # We want to store results separately for each browser
    browserName = getBrowserName(request.env.http_user_agent)
    date = str(request.utcnow)[:-16]
    time = str(request.utcnow)[11:-10]
    time = time.replace(':','-')

    # Write out results
    outputDir = os.path.join(request.folder, 'static', 'selenium', 'results')
    metadataFile = '%s-%s-%s-metadata.txt' % (date, time, browserName)
    dataFile = '%s-%s-%s-results.html' % (date, time, browserName)
    
    #xmlText = '<selenium result="' + result + '" totalTime="' + totalTime + '" successes="' + numberOfCommandSuccesses + '" failures="' + numberOfCommandFailures + '" errors="' + numberOfCommandErrors + '" />'
    f = open(os.path.join(outputDir, metadataFile), 'w')
    for key in request.vars.keys():
        if 'testTable' in key or key in ['log','suite']:
            pass
        else:
            print >> f, '%s: %s' % (key, request.vars[key])
    f.close()

    f = open(os.path.join(outputDir, dataFile), 'w')
    print >> f, suiteTable
    for testTable in testTables:
        print >> f, '<br/><br/>'
        print >> f, testTable
    f.close()
    
    message = DIV(P('Results have been successfully posted to the server here:'),
        P(A(metadataFile, _href=URL(r=request, c='static', f='selenium', args=['results', metadataFile]))),
        P(A(dataFile, _href=URL(r=request, c='static', f='selenium', args=['results', dataFile]))))
    
    response.view = 'display.html'
    title = T('Test Results')
    return dict(module_name=module_name, title=title, item=message)
