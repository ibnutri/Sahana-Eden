# -*- coding: utf-8 -*-

#
# NIM Nursing Information Manager
#
# created 2009-12-01 by nursix
#

module = 'nim'

# Current Module (for sidebar title)
try:
    module_name = db(db.s3_module.name==module).select().first().name_nice
except:
    module_name = T('Nursing Information Manager')

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Search for a Person'), False,  URL(r=request, f='person', args=['search_simple'])],
    [T('Person Details'), False, URL(r=request, f='person', args='read'),[
        [T('Basic Details'), False, URL(r=request, f='person', args='read')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='pe_contact')],
        [T('Whereabouts'), False, URL(r=request, f='person', args='presence')],
    ]],
    [T('Anamnesis'), False, URL(r=request, f='person', args=['anamnesis']),[
        [T('Disabilities'), False, URL(r=request,  f='person', args=['disabilities'])],
        [T('Diseases'), False, URL(r=request,  f='person', args=['diseases'])],
        [T('Injuries'), False, URL(r=request,  f='person', args=['injuries'])],
        [T('Treatments'), False, URL(r=request,  f='person', args=['treatments'])],
    ]],
    [T('Status'), False, URL(r=request, f='person', args=['care_status_physical']),[
        [T('Physical'), False, URL(r=request, f='person', args=['care_status_physical'])],
        [T('Mental'), False, URL(r=request, f='person', args=['care_status_mental'])],
        [T('Social'), False, URL(r=request, f='person', args=['care_status_social'])],
        [T('ADL'), False, URL(r=request, f='person', args=['care_status_adl'])],
    ]],
    [T('Care Report'), False, URL(r=request, f='person', args=['care_report_measures']),[
        [T('Problems'), False, URL(r=request, f='person', args=['care_report_problems'])],
        [T('Measures'), False, URL(r=request, f='person', args=['care_report_measures'])],
        [T('Planning'), False, URL(r=request, f='person', args=['care_report_planning'])],
    ]],
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)

# Main controller functions
def person():
    db.pr_pd_general.est_age.readable=False
    crud.settings.delete_onaccept = shn_pentity_ondelete
    return shn_rest_controller('pr', 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        list_fields=['id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'opt_pr_nationality'],
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ),
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_person, entity_type=1))

