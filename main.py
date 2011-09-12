#  _       _        _     _
# | |     | |      | |   | |
# | |__  _| |_  ___| |__ | | ___ ___ ___
# | '_ \| | __|/ __| '_ \| |/ _ | __/ __|
# | | | | | |_| (__| | | | |  __|__ \__ \
# |_| |_|_|\__|\___|_| |_|_|\___|___/___/
#
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import db
import gdata.contacts.service
import gdata.alt.appengine
import wsgiref.handlers
import gdata.docs.data
import gdata.contacts
import gdata.calendar
import gdata.service
import gdata.auth
import StringIO
import cStringIO
import datetime
import atom.url
import atom.core
import hashlib
import time
import atom
import cgi
import os
import sys

import settings
from gconnect import Gconnection


# MODELS
# TODO expand on client model to include all supported fields
class Clients(db.Model):
    business = db.StringProperty()
    name = db.StringProperty()
    title = db.StringProperty()
    email = db.StringProperty()
    credit = db.FloatProperty()
    notes = db.StringProperty()
class Services(db.Model):
    rate = db.IntegerProperty()
    rateunit = db.StringProperty()
    service = db.StringProperty()
    active = db.BooleanProperty()
#TODO figure out projects status definitions
#TODO Um, hello? start/end dates are strings?
class Projects(db.Model):
    client = db.ReferenceProperty(Clients)
    pname = db.StringProperty()
    calendarid = db.StringProperty()
    status = db.StringProperty(choices=set(["empty", "normal", "hold"]))
    spent = db.FloatProperty()
    billed = db.FloatProperty()
    budget = db.FloatProperty()
    startdate = db.StringProperty()
    enddate = db.StringProperty()
#TODO Um, hello? date is a string?
class Time(db.Model):
    project = db.ReferenceProperty(Projects)
    date = db.StringProperty()
    service = db.StringProperty()
    rate = db.IntegerProperty()
    rateunit = db.StringProperty()
    hours = db.FloatProperty()
    total = db.StringProperty()
    worker = db.StringProperty()
    note = db.StringProperty(multiline=True)
    status = db.StringProperty(choices=set(["logged", "draft", "invoiced"]))
#TODO Um, hello? date is a string?
class Invoices(db.Model):
    client = db.ReferenceProperty(Clients)
    date = db.StringProperty()
    status = db.StringProperty(choices=set(["draft", "invoiced", "paid", "sent", "deleted"]))
    notes = db.StringProperty(multiline=True)
    totalhours = db.FloatProperty()
    totalbill = db.FloatProperty()
    docslink = db.StringProperty()
    checksum = db.StringProperty()
    inum = db.IntegerProperty()

# TODO Um, hello? date is a string?
class InvoiceTime(db.Model):
    invoice = db.ReferenceProperty(Invoices)
    project = db.ReferenceProperty(Projects)
    service = db.StringProperty()
    rate = db.FloatProperty()
    rateunit = db.StringProperty()
    hours = db.FloatProperty()
    total = db.StringProperty()
    date = db.StringProperty()
    worker = db.StringProperty()
    note = db.StringProperty(multiline=True)

# And so it begins ...
class MainPage(webapp.RequestHandler):


    def get(self):
        user = users.get_current_user()
        if user:
            clients_query = Clients.all()
            clientlist = clients_query.fetch(100)
            if self.request.get('sync'):
                gclients = Client()
                ssynk = gclients.synchro()
            else:
                ssynk = ''
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            template_values = {
                'syncmessage': ssynk,
                'clients': clientlist,
                'username': user.nickname(),
                'useremail': user.email(),
                'url': url,
                'url_linktext': url_linktext
            }
            path = os.path.join(os.path.dirname(__file__), 'views/clients.html')
            self.response.out.write(template.render(path, template_values))
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            template_values = {
                'url': url,
                'url_linktext': url_linktext,
            }
            path = os.path.join(os.path.dirname(__file__), 'views/index.html')
            self.response.out.write(template.render(path, template_values))

class Service(webapp.RequestHandler):


    def post(self):
        service = str(self.request.get('service'))
        rateunit = str(self.request.get('rateunit'))
        rate = int(self.request.get('rate'))
        client = Services()
        client.rate = rate
        client.service = service
        client.rateunit = rateunit
        client.active = True
        client.put()
        action = '/'
        self.redirect(action)

class Client(webapp.RequestHandler):


    def get(self):
        gconnect = Gconnection()
        grouplist = gconnect.groups()
        template_values = {
            'groups': grouplist,
            }
        path = os.path.join(os.path.dirname(__file__), 'views/client-group.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        client = Clients()
        client.business = self.request.get('business')
        client.name = self.request.get('name')
        client.title = self.request.get('title')
        client.email = self.request.get('email')
        client.notes = self.request.get('notes')
        client.put()
        action = '/?sync=1'
        self.redirect(action)

    def synchro(self):
        try:
            clientlist = list()
            gconnect = Gconnection()
            contactlist = gconnect.contacts()
            response = list()
            for contact in contactlist:
              local_query = Clients.all()
              local_query.filter('business =', contact[0])
              local = local_query.fetch(100)
              if local:
                for foo in local:
                  if foo.email == contact[3]:
                    foobar = ''
                  else:
                    client_query = Clients.gql("WHERE business = :1",foo.business)
                    client_result = client_query.fetch(1)
                    client = client_result[0]
                    client.email = db.Text(contact[3])
                    client.put()
                    foobar = [foo.business+' Updated']
                    response.append(foobar)
              else:
                response.append(contact)
            return response
        except:
            response = ''
            return response

class Dashboard(webapp.RequestHandler):


    def get(self):
        user = users.get_current_user()
        if user:
            all_clients_query = Clients.all()
            all_clients = all_clients_query.fetch(100)
            services_query = Services.all()
            # TODO: make the filter below work, and 
            # add UI to disable services
            #services_query.filter('active =', 'True')
            services = services_query.fetch(100)
            k = db.Key(self.request.get('clientkey'))
            clients_query = Clients.all()
            clients_query.filter('__key__ = ', k)
            client = clients_query.fetch(1)
            projects_query = Projects.all()
            projects_query.filter('client =', k)
            projects = projects_query.fetch(100)
            invoices_query = Invoices.all()
            invoices_query.filter('client =', k)
            invoices_query.filter('status != ', 'deleted')
            invoices = invoices_query.fetch(100)
            if users.get_current_user():
                url = users.create_logout_url(self.request.uri)
                url_linktext = 'Logout'
            else:
                url = users.create_login_url(self.request.uri)
                url_linktext = 'Login'
            template_values = {
                'title': settings.APP['title'],
                'author': settings.APP['author'],
                'allclients': all_clients,
                'client': client,
                'services': services,
                'projectkeys': projects,
                'invoices': invoices,
                'clientname': self.request.get('clientname'),
                'clientkey': self.request.get('clientkey'),
                'url': url,
                'url_linktext': url_linktext,
                }
            path = os.path.join(os.path.dirname(__file__), 'views/dashboard.html')
            self.response.out.write(template.render(path, template_values))
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            template_values = {
                'url': url,
                'url_linktext': url_linktext,
            }
            path = os.path.join(os.path.dirname(__file__), 'views/index.html')
            self.response.out.write(template.render(path, template_values))

class Project(webapp.RequestHandler):


    def get(self):
        if(self.request.get('action') == "delete"):
            p = db.Key(self.request.get('pid'))
            db.delete(p)
            #self.request.get('cid')
            self.response.out.write("Project deleted.")
        else:
            self.response.out.write("No action for this yet.")

    def post(self):
        calendar_link = ""
        if(settings.APP['gcalenabled']):
            ck = db.Key(self.request.get('clientkey'))
            ck_query = Clients.all()
            ck_query.filter('__key__ =', ck)
            client = ck_query.fetch(1)
            clientname = client[0].business
            try:
              cal_title = self.request.get('pname') + " - " + clientname
              projectdesc = 'Client: ' + clientname + ' Project: ' + self.request.get('pname')
              gconnect = Gconnection()
              gd_client = gconnect.calendar_connect()
              calendar = gdata.calendar.CalendarListEntry()
              calendar.title = atom.Title(text=cal_title)
              calendar.summary = atom.Summary(text=projectdesc)
              calendar.where = gdata.calendar.Where(value_string=settings.COMPANY["city"])
              calendar.color = gdata.calendar.Color(value='#2952A3')
              calendar.timezone = gdata.calendar.Timezone(value='America/Los_Angeles')
              calendar.hidden = gdata.calendar.Hidden(value='false')
              new_calendar = gd_client.InsertCalendar(new_calendar=calendar)
              calendar_link = new_calendar.link[0].href
            except:
              # TODO figure out proper action to take
              calendar_link = "Something went wrong."
        projects = Projects()
        projects.client = db.Key(self.request.get('clientkey'))
        projects.pname = self.request.get('pname')
        projects.calendarid = calendar_link
        projects.status = 'empty'
        projects.summary = 0
        projects.put()
        action = '/dashboard?clientkey=' + self.request.get('clientkey') + '#projects'
        self.redirect(action)

class Timesheet(webapp.RequestHandler):


    def get(self):
        if(self.request.get('action') == "delete"):
            k = db.Key(self.request.get('tid'))
            db.delete(k)
        pi = db.Key(self.request.get('pid'))
        time_query = Time.all()
#         time_query.filter('status =', 'logged')
        time_query.filter('project =', pi)
        time = time_query.fetch(100)
        totalhours = 0
        for hours in time:
            totalhours = int(hours.hours) + totalhours
        rate = 45
        subtotal = totalhours * rate
        taxrate = .12
        tax = subtotal * taxrate
        totalinvoice = subtotal + tax
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'time': time,
            'totalhours': totalhours,
            'subtotal': subtotal,
            'tax': tax,
            'totalinvoice': totalinvoice,
            'pid': self.request.get('pid'),
            'url': url,
            'url_linktext': url_linktext
            }
        path = os.path.join(os.path.dirname(__file__), 'views/timesheet-ajah.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):

        # I'm not sure why I have to import this here, but it throws errors
        # if I do it at the top
        from datetime import datetime, timedelta
        # Calculate dates and times.
        # The submitting form has service, project, date, note, and 
        # multiplier (hours) fields. It is assumed that you log your time 
        # when you *finish* a task and subtract the amount of time (multiplier) 
        # that you just spent on  it. You can, of course override "now" and 
        # provide the end time manually, but the base assumption is that you 
        # take the given time and *subtract* the multiplier (hours).
        hours = float(self.request.get('hours'))
        # First, we check to see if we're overriding our "now" assumption
        # if we are, we have to append :00 onto the time (as the datetime html5
        # input doesn't seem to support the full this) to conform to 
        # the gdata API; otherwise, we take GMT and format it accoringly so
        # that we can do the math
        if self.request.get('date'):
            end_time = self.request.get('date') + ":00"
        else:
            end_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        the_end = datetime.strptime(end_time,'%Y-%m-%dT%H:%M:%S')
        # adjust for timezone
        # TODO refactor to support Eastern timezones as this breaks if you
        # use a positive GMT offset. 
        ender = the_end - timedelta(hours=settings.CAL["GMToffset"])
        # subtract the hours spent
        the_start = ender - timedelta(hours=hours)
        #format things for calendar API (add the T)
        event_end = str(ender).replace(" ", "T")
        event_start = str(the_start).replace(" ", "T")
        # Get project details from projects model
        projectid = db.Key(self.request.get('pid'))
        project_query = Projects.all()
        project_query.filter('__key__ =', projectid)
        projects = project_query.fetch(1)
	# Get the calendar ID so that we can post
        # to it and add this event to the appropriate calendar
        calendar_uri = projects[0].calendarid
        # Update the project status to reflect that it now has billable time.
	# If we don't do this, we won't be able to select the project in the UI
	# as we test for project status; if it's "empty" the checkbox is
	# disabled.
	projects[0].status = 'normal'
	projects[0].put()
        # put together time details to go into time model
        rateservice = str(self.request.get('service')).split(" || ")
        linetotal = int(rateservice[1]) * float(self.request.get('hours'))
        linetotal = "%.2f" % linetotal
        entry = Time()
        entry.project = projectid
        entry.date = event_start
        entry.hours = float(self.request.get('hours'))
        entry.service = rateservice[0]
        entry.rate = int(rateservice[1])
        entry.rateunit = rateservice[2]
        entry.total = str(linetotal)
        entry.worker = self.request.get('worker')
        entry.note = self.request.get('note')
        entry.status = 'logged'
        entry.put()
        # if gcalendar is enabled, use the gdata API to add event to 
        # this project's calendar
        if(settings.APP["gcalenabled"]):
            gconnect = Gconnection()
            gd_client = gconnect.calendar_connect()
            location = settings.APP["title"]
            title = rateservice[0]
            # TODO figure out pep8 formatting for below
            desc = self.request.get('note') + "\nWorker: " + self.request.get('worker') + "\nHours: " + self.request.get('hours')
            event_entry = gdata.calendar.CalendarEventEntry()
            event_entry.title = atom.Title(text=title)
            event_entry.content = atom.Content(text=desc)
            event_entry.timezone = gdata.calendar.Timezone(value='America/Los_Angeles')
            event_entry.when.append(gdata.calendar.When(start_time=event_start, end_time=event_end))
            event_entry.where.append(gdata.calendar.Where(value_string=location))
            try:
                cal_event = gd_client.InsertEvent(event_entry,calendar_uri)
            except gdata.service.RequestError, request_exception:
                request_error = request_exception[0]
                if request_error['status'] == 401 or request_error['status'] == 403:
                    self.response.out.write("401 or 403")
                else:
                    raise
        action = '/timesheet?pid=' + self.request.get('pid')
        self.redirect(action)

class Invoice(webapp.RequestHandler):


    def get(self):
        if (self.request.get('action') == "delete"):
            i = db.Key(self.request.get('iid'))
            deleteit = db.get(i)
            deleteit.status = 'deleted'
            deleteit.put()
            # TODO Figure this shit out so we're not orphaning a bunch of records in the invoicetime model
            # TODO We also want to revert the statuses in the Time model records
            # IDEA: Maybe write a garbage collector routine that runs daily or whatever
            # itime = InvoiceTime.all()
            # itime.filter("invoice", i)
            # itime.delete()
            action = '/dashboard?clientkey=' + self.request.get('cid')
            self.redirect(action)
        if (self.request.get('action') == "send"):
	    # Get invoice details
	    invoiceid = db.Key(self.request.get('iid'))
	    invoice_query = Invoices.all()
	    invoice_query.filter("__key__", invoiceid)
	    invoice = invoice_query.fetch(1)
	    invoicekey = str(invoiceid)
	    invoicetotal = str(invoice[0].totalbill)
	    
            # Get client information
	    ck = db.Key(self.request.get('cid'))
            ck_query = Clients.all()
            ck_query.filter('__key__ =', ck)
            client = ck_query.fetch(1)
            clientname = client[0].business
	    clientemail = client[0].email
	    # Calculate a checksum for the invoice.
            # This should be more better thought out (sic), but the idea
	    # is that we need a way to veryify with the client that the invoice
	    # they're viewing (when they view it) is the original invoice that
	    # was sent to them.
	    # I tried hashing the entire HTML contents of a given invoice, but
	    # quickly ran into problems that way. In the meantime, we're just
	    # going to hash the clients name (with spaces removed), the date, and
	    # the total amount of the invoice.
	    # TODO fill the hash with complete invoice details _somehow_
	    # TODO store the resulting QR code as a blob?
	    businessname = str(client[0].business).replace(" ", "")
            checkthatsum = businessname + invoice[0].date + invoicetotal
            invoicechecksum = hashlib.md5(checkthatsum).hexdigest()
	    invoice[0].checksum = invoicechecksum
	    invoice[0].status = "sent"
	    invoice[0].put()
            invoiceurl = settings.APP["URL"] + "invoice-gen?ichecksum=" +  invoicechecksum
            qrurl = "http://chart.apis.google.com/chart?cht=qr&chs=300x300&chl="+invoiceurl+"&chld=H|0"
            qrattach = urlfetch.fetch(qrurl)
	    qrattachname = invoicechecksum + ".png"
	    emailsubject = "Invoice #" + str(invoice[0].inum) + " for $" + invoicetotal
            message = mail.EmailMessage(sender="Hitchless Web Design <allan@hitchless.com>",
                                        subject=emailsubject)
            message.to = "Allan Kenneth <allankh@gmail.com>"
            message.attachments = [(qrattachname,qrattach.content)]
            message.body = "Dear " + clientname + ",\n\n"
	    message.body += "To view your invoice, please click the link below:\n"
            message.body += invoiceurl
            message.send()
            # TODO lol
	    self.response.out.write("yeah?")
        else:
            i = db.Key(self.request.get('iid'))
            times_query = InvoiceTime.all()
            times_query.filter('invoice =', i)
            times = times_query.fetch(100)
            totalhours = 0
            subtotal = 0
            for hours in times:
                totalhours = totalhours + float(hours.hours)
                subtotal = subtotal + float(hours.total)
            taxrate = .12
            tax = subtotal * taxrate
            totalinvoice = subtotal + tax

            # format the values to two decimal places before sending to template
            subtotal = "%.2f" % subtotal
            tax = "%.2f" % tax
            totalinvoice = "%.2f" % totalinvoice
            
            logopath = settings.COMPANY['logopath']
            
            template_values = {
                'times': times,
                'totalhours': totalhours,
                'subtotal': subtotal,
                'tax': tax,
                'totalinvoice': totalinvoice,
                'logopath': logopath,
                'companyname': settings.COMPANY['name'],
                'companyaddress': settings.COMPANY['street'],
                'companycity': settings.COMPANY['city'],
                'companyprovince': settings.COMPANY['province'],
                'companycode': settings.COMPANY['code']
                }
            path = os.path.join(os.path.dirname(__file__), 'views/invoice.html')
            self.response.out.write(template.render(path, template_values))

    def post(self):
        if self.request.get('action') == 'statusupdate':
          i = db.Key(self.request.get('iid'))
          update = db.get(i)
          update.status = self.request.get('status')
          update.put()
          action = '/dashboard?clientkey=' + self.request.get('clientkey')
          self.redirect(action)
        else:
            import time
            date = time.strftime('%Y-%m-%d', time.gmtime())
            k = db.Key(self.request.get('clientkey'))
            invoice = Invoices()
            invoice.client = k
            invoice.date = date
            invoice.status = 'draft'
            invoice.total = 0.00
            invoice.put()
            iid = invoice.key()
            invoiceid = str(invoice.inum)
            billedtotal = 0.00
            billedtime = 0.00
            # there is a form that lists the projects, allowing the user to check one or more
            # the field data is the key for that project
            # get_all gives an array of keys returned which we want to pull time from
            projects = self.request.get_all('projects')
            # start looping through the keys
            for projectkey in projects:
              # make the string key an actual key object
              pkey = db.Key(projectkey)
              # get everything out of the time store with that project associated
              # and which has a status of logged
              times_query = Time.all()
              times_query.filter('project =', pkey)
              times_query.filter('status =', 'logged')
              times = times_query.fetch(100)
              # setup some variables for below
              status = []
              # now looping through the times
              # we're going to copy each time entry into the invoiceTime model
              for time in times:
                billedtime = float(billedtime) + float(time.hours)
                billedtotal = float(billedtotal) + float(time.total)
                itime = InvoiceTime()
                itime.invoice = iid
                itime.project = pkey
                itime.date = time.date 
                itime.hours = time.hours
                itime.rate = float(time.rate)
                itime.rateunit = time.rateunit
                itime.service = time.service
                newtotal = float(time.total)
                newtotal = "%.2f" % newtotal
                itime.total = newtotal
                itime.worker = time.worker
                itime.note = time.note
                itime.put()
                time.status = "invoiced"
                status.append(time)
              db.put(status)
              project_update = db.get(pkey)
              project_update.status = "empty"
              project_update.put()
            invoice_update = db.get(iid)
            invcount = Invoices.all(keys_only=True)
            count = invcount.count()
	    inumb = count + 1
            totalhoursbilled = "%2.f" % billedtime
            totalbill = "%.2f" % billedtotal
            invoice_update.totalhours = float(totalhoursbilled)
            invoice_update.totalbill = float(totalbill)
	    invoice_update.inum = inumb
            invoice_update.put()
            project_update = db.get(pkey)
            project_update.billed = billedtime
            project_update.put()
            action = '/invoice?iid=' + str(iid)            
            self.redirect(action)

class InvoiceGenerate(webapp.RequestHandler):


    def get(self):
        # This needs A LOT of work. We don't really want to give 
	# the client the invoice key; the link we send them uses
	# the checksum. In the following, we simply redirect to
	# the actual invoice, but at some point this will change.
	# I'm thinking that I'll require the client to set a salt
	# when they're added to the system, and that, once they 
	# click the link, they'll be prompted for the salt ...
        i = self.request.get('ichecksum')
	inv = Invoices.all(keys_only=True)
	inv.filter('checksum =', i)
	invoice = inv.fetch(1)
	foo = '<a href="/invoice?iid=' + str(invoice[0]) + '">Go to invoice</a>. FOOBAR'
	self.response.out.write(foo)
 

application = webapp.WSGIApplication([
                                      ('/', MainPage),
                                      ('/client', Client),
                                      ('/dashboard', Dashboard),
                                      ('/timesheet', Timesheet),
                                      ('/invoice', Invoice),
                                      ('/invoice-gen', InvoiceGenerate),
				      ('/project', Project),
                                      ('/service', Service)
                                     ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
