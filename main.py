#  _       _        _     _
# | |     | |      | |   | |
# | |__  _| |_  ___| |__ | | ___ ___ ___
# | '_ \| | __|/ __| '_ \| |/ _ | __/ __|
# | | | | | |_| (__| | | | |  __|__ \__ \
# |_| |_|_|\__|\___|_| |_|_|\___|___/___/
#
# @author: allan@hitchless.com

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import conversion
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


class Projects(db.Model):
    #TODO figure out projects status definitions
    #TODO Um, hello? start/end dates are strings?
    client = db.ReferenceProperty(Clients)
    pname = db.StringProperty()
    calendarid = db.StringProperty()
    status = db.StringProperty(choices=set(["empty", "normal", "hold"]))
    spent = db.FloatProperty()
    billed = db.FloatProperty()
    budget = db.FloatProperty()
    startdate = db.StringProperty()
    enddate = db.StringProperty()





class Invoices(db.Model):

    statuses = ["draft", "invoiced", "paid", "sent", "deleted"]
    client = db.ReferenceProperty(Clients)
    date = db.DateTimeProperty()
    status = db.StringProperty(choices=set(statuses))
    notes = db.StringProperty(multiline=True)
    totalhours = db.FloatProperty()
    totalbill = db.FloatProperty()
    docslink = db.StringProperty()
    checksum = db.StringProperty()
    inum = db.IntegerProperty()
    qrlink = db.BlobProperty()
    qrchecksum = db.BlobProperty()

class Time(db.Model):
    client = db.ReferenceProperty(Clients)
    invoice = db.ReferenceProperty(Invoices)
    project = db.ReferenceProperty(Projects)
    date = db.DateTimeProperty()
    service = db.StringProperty()
    rate = db.IntegerProperty()
    rateunit = db.StringProperty()
    hours = db.FloatProperty()
    total = db.StringProperty()
    worker = db.StringProperty()
    note = db.StringProperty(multiline=True)
    status = db.StringProperty(choices=set(["logged", "draft", "invoiced"]))
    
    
    
    
    
    
    
    


class MainPage(webapp.RequestHandler):
    # And so it begins ...
    def get(self):
        user = users.get_current_user()
        if user:
            clients_query = Clients.all()
            clientlist = clients_query.fetch(100)
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            template_values = {
                'clients': clientlist,
                'username': user.nickname(),
                'useremail': user.email(),
                'url': url,
                'url_linktext': url_linktext
            }
            path = os.path.join(os.path.dirname(__file__),
                                'views/clients.html')
            self.response.out.write(template.render(path, template_values))
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            template_values = {
                'url': url,
                'url_linktext': url_linktext,
            }
            path = os.path.join(os.path.dirname(__file__), 
                                'views/index.html')
            self.response.out.write(template.render(path, template_values))


class ClientHandler(webapp.RequestHandler):

    def post(self):
        client = Clients()
        client.business = self.request.get('business')
        client.name = self.request.get('name')
        client.title = self.request.get('title')
        client.email = self.request.get('email')
        client.notes = self.request.get('notes')
        client.put()
        
        action = '/dashboard?clientkey=' + str(client.key())
        self.redirect(action)







class DashboardHandler(webapp.RequestHandler):

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
            
            time_query = Time.all()
            time_query.filter('client =', k)
            time_query.order('-project')
            times = time_query.fetch(100)

            projects_query = Projects.all()
            projects_query.filter('client =', k)
            projects = projects_query.fetch(100)

            invoices_query = Invoices.all()
            invoices_query.filter('client =', k)
            # invoices_query.filter('status != ', 'deleted')
            invoices_query.order('-inum')
            invoices = invoices_query.fetch(100)

            statuses = ["draft", "invoiced", "paid", "sent", "deleted"]
            if users.get_current_user():
                url = users.create_logout_url(self.request.uri)
                url_linktext = 'Logout'
            else:
                url = users.create_login_url(self.request.uri)
                url_linktext = 'Login'
            
            template_values = {
                'statuses': statuses,
                'title': settings.APP['title'],
                'author': settings.APP['author'],
                'times': times,
                'allclients': all_clients,
                'client': client,
                'businessname': client[0].business,
                'services': services,
                'invoices': invoices,
                'projectkeys': projects,
                'pslug': self.request.get('p'),
                'clientname': self.request.get('clientname'),
                'clientkey': self.request.get('clientkey'),
                'url': url,
                'url_linktext': url_linktext,
                }
            path = os.path.join(os.path.dirname(__file__), 
                                'views/dash.html')
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







class ProjectsHandler(webapp.RequestHandler):

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
            
            time_query = Time.all()
            time_query.filter('client =', k)
            time_query.order('-project')
            times = time_query.fetch(100)

            projects_query = Projects.all()
            projects_query.filter('client =', k)
            projects = projects_query.fetch(100)
            

            statuses = ["draft", "invoiced", "paid", "sent", "deleted"]
            if users.get_current_user():
                url = users.create_logout_url(self.request.uri)
                url_linktext = 'Logout'
            else:
                url = users.create_login_url(self.request.uri)
                url_linktext = 'Login'
            template_values = {
                'statuses': statuses,
                'title': settings.APP['title'],
                'author': settings.APP['author'],
                'times': times,
                'allclients': all_clients,
                'client': client,
                'businessname': client[0].business,
                'services': services,
                'projectkeys': projects,
                'pslug': self.request.get('p'),
                'clientname': self.request.get('clientname'),
                'clientkey': self.request.get('clientkey'),
                'url': url,
                'url_linktext': url_linktext,
                }
            path = os.path.join(os.path.dirname(__file__), 
                                'views/projects.html')
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


class ProjectHandler(webapp.RequestHandler):
    def get(self):
        if(self.request.get('action') == "delete"):
            p = db.Key(self.request.get('pid'))
            db.delete(p)
            action = '/dashboard?clientkey=' + self.request.get('cid') + ''
            self.redirect(action)
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
                projectdesc = 'Client: ' + clientname + ' '
                projectdesc += 'Project: ' + self.request.get('pname')
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
        action = '/dashboard?clientkey=' + self.request.get('clientkey')
        self.redirect(action)


class ServiceHandler(webapp.RequestHandler):
    def get(self):
        if(self.request.get('action') == "delete"):
            service = db.Key(self.request.get('sid'))
            db.delete(service)
            action = '/dashboard?clientkey=' + self.request.get('clientkey')
            self.redirect(action)
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
        action = '/dashboard?clientkey=' + self.request.get('clientkey')
        self.redirect(action)

class AddTimesHandler(webapp.RequestHandler):

    def get(self):

        k = db.Key(self.request.get('clientkey'))
        
        clients_query = Clients.all()
        clients_query.filter('__key__ = ', k)
        client = clients_query.fetch(1)
        
        services_query = Services.all()
        # TODO: make the filter below work, and 
        # add UI to disable services

        #services_query.filter('active =', 'True')
        services = services_query.fetch(100)

        projects_query = Projects.all()
        projects_query.filter('client =', k)
        projects = projects_query.fetch(100)

        all_clients_query = Clients.all()
        all_clients = all_clients_query.fetch(100)

        template_values = {
            'client': client,
            'businessname': client[0].business,
            'allclients': all_clients,
            'projectkeys': projects,
            'services': services,
        }

        path = os.path.join(os.path.dirname(__file__), 'views/timesheet-form.html')
        self.response.out.write(template.render(path, template_values))
            
            
class TimesheetHandler(webapp.RequestHandler):

    def get(self):
        if(self.request.get('action') == "delete"):
            # Delete that thing!
            k = db.Key(self.request.get('tid'))
            db.delete(k)
            # If the project doesn't have any other outstanding time
            # to be invoiced, update its status so the UI reflects that.
            # It's expensive, but necessary.
#             projectid = db.Key(self.request.get('pid'))
#             time_query = Time.all()
#             time_query.filter('project =', projectid)
#             time_query.filter('status =', 'logged')
#             time_query.order('-date')
#             time = time_query.fetch(10)
#             if not time:
#                 project_query = Projects.all()
#                 project_query.filter('__key__ =', projectid)
#                 projects = project_query.fetch(1)
#                 projects[0].status = 'empty'
#                 projects[0].put()
#             action = '/dashboard?clientkey=' + self.request.get('cid')
#             self.redirect(action)



        else:
            pi = db.Key(self.request.get('pid'))
            time_query = Time.all()
            time_query.filter('project =', pi)
#             time_query.filter('status =', 'logged')
            time_query.order('-date')
            time = time_query.fetch(100)
            totalhours = 0
            for hours in time:
                totalhours = int(hours.hours) + totalhours
            rate = 45
            subtotal = totalhours * rate
            taxrate = .12
            tax = subtotal * taxrate
            totalinvoice = subtotal + tax
            template_values = {
                'time': time,
                'totalhours': totalhours,
                'subtotal': subtotal,
                'tax': tax,
                'totalinvoice': totalinvoice,
                'pid': self.request.get('pid')
            }
            path = os.path.join(os.path.dirname(__file__), 'views/timesheet-ajah.html')
            self.response.out.write(template.render(path, template_values))

    def post(self):
        # Philosophically, posting new time assumes that you are logging 
        # your time as you finish the task at hand. You can override this
        # behavior by providing a date/time, but that timestamp is 
        # still assumed to be the end point of the task, and the amount
        # of time entered is subtracted from it.
        #
        # I'm not sure why I have to import this here, but it throws errors
        # if I do it at the top;
        # TODO get someone to explain why.
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
        #    end_time = self.request.get('date') + ":00"
            end_time = self.request.get('date')
        else:
            end_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        the_end = datetime.strptime(end_time,'%Y-%m-%dT%H:%M:%S')

        # Adjust for timezone.
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
        entry.client = db.Key(self.request.get('clientkey'))
        entry.project = projectid
        entry.date = the_end
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
            desc = self.request.get('note')
            desc += "\nWorker: " + self.request.get('worker')
            desc += "\nHours: " + self.request.get('hours')
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
        #action = '/dashboard?clientkey=' + self.request.get('clientkey')
        import unicodedata
        import re
        s = projects[0].pname
        slug = unicodedata.normalize('NFKD', s)
        slug = slug.encode('ascii', 'ignore').lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
        slug = re.sub(r'[-]+', '-', slug)
        action = '/dashboard?clientkey=' + self.request.get('clientkey') + '&p=' + slug
        self.redirect(action)


class InvoicesHandler(webapp.RequestHandler):
    def get(self):

        k = db.Key(self.request.get('clientkey'))
        
        invoices_query = Invoices.all()
        invoices_query.filter('client =', k)
        # invoices_query.filter('status != ', 'deleted')
        invoices_query.order('-inum')
        invoices = invoices_query.fetch(100)

        all_clients_query = Clients.all()
        all_clients = all_clients_query.fetch(100)

        services_query = Services.all()
        # TODO: make the filter below work, and 
        # add UI to disable services
        #services_query.filter('active =', 'True')
        services = services_query.fetch(100)


        clients_query = Clients.all()
        clients_query.filter('__key__ = ', k)
        client = clients_query.fetch(1)

        template_values = {
            'services': services,
            'invoices': invoices,
            'allclients': all_clients,
            'client':  client,
            'businessname': client[0].business
            }
        path = os.path.join(os.path.dirname(__file__), 
                            'views/invoices.html')
        self.response.out.write(template.render(path, template_values))

class InvoiceHandler(webapp.RequestHandler):
    def get(self):
        message = ''
        if (self.request.get('action') == "delete"):
            # At the moment, we don't want to actually delete real numbered 
            # invoices from the datastore, as it will adversly effect how 
            # I've implemented the invoice numbering; we can't handle
            # real sequential numbering without resorting to sharding
            # (as per stackoverflow on this topic); for the time being
            # we're just running an all.count() + 1 on the invoices model,
            # filtering out drafts.
            # If we actually delete stuff, we could get an invoice issued
            # after the last count, but with a smaller invoice number
            # TODO perhaps zero out the other fields to avoid confusion?
            i = db.Key(self.request.get('iid'))
            deleteit = db.get(i)
            # First, let's check to see if this invoice has had an inum 
            # assigned to it; if it does, then we just assign the status
            # as deleted; if it doesn't have an inum, then it's safe
            # to remove the entry from the datastore entirely.
            if deleteit.inum:
                deleteit.status = 'deleted'
                deleteit.put()
            else:
                deleteit.delete()
            # TODO Revert the statuses in the associated Time model records too
            
            # IDEA: Maybe write a garbage collector routine that runs daily 
            #       or whatever
            # itime = InvoiceTime.all()
            # itime.filter("invoice", i)
            # itime.delete()
            action = '/invoices?clientkey=' + self.request.get('cid')
            self.redirect(action)
        if (self.request.get('action') == "finalize"):
            # When we first create an invoice, we leave a few things blank,
            # including the checksum and real invoice number.
            # With this action, we complete the process by generating
            # what's missing and thus preparing the invoice to be sent.
            # First, get invoice details.
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
            # Get a keys-only (for speed) query of all the invoices
            # in the datastore that have an inum issued to them.
            # Take that count and add 1 to it to get the new inum.
            invcount = Invoices.all(keys_only=True)
            invcount.filter("inum >",0)
            count = invcount.count()
            inumber = count + 1
            invoice[0].inum = inumber
            # Calculate a checksum for the invoice.
            # This should be more-better (sic) thought out, but the idea
            # is that we need a way to veryify with the client that the invoice
            # they're viewing (when they view it) is the original invoice that
            # was sent to them.
            # Hash the clients name, the date, 
            # and the total amount of the invoice.
            # TODO fill the hash with complete invoice details _somehow_
            checkthatsum = clientname + str(invoice[0].date) + invoicetotal
            invoicechecksum = hashlib.md5(checkthatsum).hexdigest()
            invoice[0].checksum = invoicechecksum
            invoice[0].status = "invoiced"
            try:
                # Use the Google Chart API to generate the QR codes.
                # TODO Investigate ways to do this that might work offline:
                # https://github.com/bernii/PyQRNativeGAE
                chartapi = "http://chart.apis.google.com/chart"
                chartapi += "?cht=qr&chs=300x300&chld=H|0&chl="
                invoiceurl = settings.APP["URL"]
                invoiceurl += "invoice-gen?ichecksum="
                invoiceurl += invoicechecksum
                qrurl = chartapi + invoiceurl
                qrchecksum = chartapi + invoicechecksum
                qrattach = urlfetch.fetch(qrurl)
                qrcheck = urlfetch.fetch(qrchecksum)
                qlink = qrattach.content
                qchk = qrcheck.content
            except:
                qlink = "offline"
                qchk = "offline"
            invoice[0].qrlink = qlink
            invoice[0].qrchecksum = qchk
            invoice[0].put()
            #message = 'Finalized.'
            message = 'Finalized. <a href="/invoice?iid='+self.request.get('iid')+'"><span class="icon-remove-sign"><span></a>'


        if (self.request.get('action') == "send"):
            # Get client information
            ck = db.Key(self.request.get('cid'))
            ck_query = Clients.all()
            ck_query.filter('__key__ =', ck)
            client = ck_query.fetch(1)
            clientname = client[0].business
            clientemail = client[0].email
            invoiceid = db.Key(self.request.get('iid'))
            invoice_query = Invoices.all()
            invoice_query.filter("__key__", invoiceid)
            invoice = invoice_query.fetch(1)
            invoice[0].status = "sent"
            invoice[0].put()
            invoicekey = str(invoiceid)
            invoicetotal = str(invoice[0].totalbill)
            invoicechecksum = invoice[0].checksum
            invoiceurl = settings.APP["URL"]
            invoiceurl += "invoice-gen?ichecksum="
            invoiceurl += invoicechecksum

            import urllib2
            response = urllib2.urlopen('http://hitchless.com/')
#             self.response.out.write(response.read())
        
            
            asset = conversion.Asset("text/html", response.read(), "invoice.html")
            conversion_obj = conversion.Conversion(asset, "application/pdf")
            
            rpc = conversion.create_rpc()
            conversion.make_convert_call(rpc, conversion_obj)
            
            result = rpc.get_result()
            if result.assets:
              # Note: in most cases, we will return data all in one asset.
              # Except that we return multiple assets for multiple pages image.
              for asset in result.assets:
                invoiceattachment = asset.data
              self.response.headers['Content-Type'] = "application/pdf"
              self.response.out.write(asset.data);

#               attachname = settings.COMPANY["name"] + "-invoice#" + str(invoice[0].inum) + ".pdf"
#               emailsubject = "Invoice #" + str(invoice[0].inum) + " for $"
#               emailsubject += invoicetotal
#               emailsender = settings.COMPANY["name"]
#               emailsender += "<" + settings.COMPANY["email"] + ">"
#               message = mail.EmailMessage(sender=emailsender, subject=emailsubject)
#               message.to = "Allan Kenneth <allankh@gmail.com>"
#               message.attachments = [(attachname,invoiceattachment)]
#               message.body = "Dear " + clientname + ",\n\n"
#               message.body += "To view your invoice, please click the link below:\n\n"
#               message.body += invoiceurl
#               message.send()
#               
            else:
                message = result.error_code + " - " + result.error_text
            
            
            
            # TODO a template or something? It's UI decision time!
            #message = 'Sent.'
            message = 'Sent. <a href="/invoice?iid='+self.request.get('iid')+'"><span class="icon-remove-sign"><span></a>'

        if self.request.get('action') == 'statusupdate':
            i = db.Key(self.request.get('iid'))
            update = db.get(i)
            update.status = self.request.get('status')
            update.put()
            message = 'Updated as ' + self.request.get('status') + '. <a href="/invoice?iid='+self.request.get('iid')+'"><span class="icon-remove-sign"><span></a>'


        # After all of the different actions to be taken,
        # we finally just print out the invoice with the appropriate message
        # at the top.


        statuses = ["draft", "invoiced", "paid", "sent", "deleted"]
        i = db.Key(self.request.get('iid'))
        times_query = Time.all()
        times_query.filter('invoice =', i)
        times = times_query.fetch(100)
        totalhours = 0
        subtotal = 0
        for hours in times:
            totalhours = totalhours + float(hours.hours)
            subtotal = subtotal + float(hours.total)
        # TODO figure out how we want to serve the images from the datastore
        # qrq = Invoices.all()
        # qrq.filter("__key__", i)
        # qr = qrq.fetch(1)
        # qrlink = qr[0].qrlink
        taxrate = settings.APP["taxrate"]
        tax = subtotal * taxrate
        totalinvoice = subtotal + tax
        # format the values to two decimal places before sending to template
        # TODO remove this because it shouldn't be necessary; they should
        # come out the datastore formatted correctly!
        # 
        # times[0].invoice.totalbill
        #
        subtotal = "%.2f" % subtotal
        tax = "%.2f" % tax
        totalinvoice = "%.2f" % totalinvoice
        logopath = settings.COMPANY['logopath']
        template_values = {
            'message': message,
            'statuses': statuses,
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
            import time
            from datetime import datetime, timedelta
            #date = time.strftime('%Y-%m-%d', time.gmtime())
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
            thedate = datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')
            k = db.Key(self.request.get('clientkey'))
            invoice = Invoices()
            invoice.client = k
            invoice.date = thedate
            invoice.status = 'draft'
            invoice.total = 0.00
            invoice.put()
            iid = invoice.key()
            invoiceid = str(invoice.inum)
            billedtotal = 0.00
            billedtime = 0.00
            # there is a form that lists the projects, allowing the user to 
            # check one or more the field data is the key for that project
            # get_all gives an array of keys returned which we want to pull 
            # time from
            projects = self.request.get_all('projects')
            # start looping through the keys
            for projectkey in projects:
                # make the string key an actual key object
                pkey = db.Key(projectkey)
                # get everything out of the time store with that project 
                # associated and which has a status of logged.
                times_query = Time.all()
                times_query.filter('project =', pkey)
                times_query.filter('status =', 'logged')
                times = times_query.fetch(100)
                
                for time in times:


                    time.invoice = iid
                    time.status = "invoiced"
                    db.put(time)

                    billedtime = float(billedtime) + float(time.hours)
                    billedtotal = float(billedtotal) + float(time.total)
                    
                project_update = db.get(pkey)
                project_update.status = "empty"
                project_update.put()
            
            

            totalhoursbilled = "%2.f" % billedtime
            totalbill = "%.2f" % billedtotal
            totalbill = float(totalbill)

            invoice_update = db.get(iid)
            invoice_update.totalhours = float(totalhoursbilled)
            invoice_update.totalbill = totalbill
            invoice_update.put()

            project_update = db.get(pkey)
            project_update.billed = billedtime
            project_update.put()
            action = '/invoice?iid=' + str(iid)            
            self.redirect(action)


class InvoiceGenerateHandler(webapp.RequestHandler):
    def get(self):
        # This needs A LOT of work. We don't really want to give 
        # the client the invoice key; the link we send them uses
        # the checksum. In the following, we simply redirect to
        # the actual invoice, but at some point this will change.
        # I'm thinking that I'll require the client to set a salt
        # when they're added to the system, and that, once they 
        # click the link, they'll be prompted for the salt ...
        # i = self.request.get('ichecksum')
        # inv = Invoices.all(keys_only=True)
        # inv.filter('checksum =', i)
        # invoice = inv.fetch(1)
        # foo = '<a href="/invoice?iid=' + str(invoice[0])
        # foo += '">Go to invoice</a>.'
        # self.response.out.write(foo)

        i = self.request.get('ichecksum')
        statuses = ["draft", "invoiced", "paid", "sent", "deleted"]
        times_query = Time.all()
        times_query.filter('checksum =', i)
        times = times_query.fetch(100)
        totalhours = 0
        subtotal = 0
        for hours in times:
            totalhours = totalhours + float(hours.hours)
            subtotal = subtotal + float(hours.total)
        taxrate = settings.APP["taxrate"]
        tax = subtotal * taxrate
        totalinvoice = subtotal + tax
        subtotal = "%.2f" % subtotal
        tax = "%.2f" % tax
        totalinvoice = "%.2f" % totalinvoice
        logopath = settings.COMPANY['logopath']
        template_values = {
            'statuses': statuses,
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
        path = os.path.join(os.path.dirname(__file__), 'views/invoice-public.html')
        self.response.out.write(template.render(path, template_values))


class GetQRLinkHandler(webapp.RequestHandler):
    def get(self):
        hashish = self.request.get('hashish')
        check = self.request.get('checksum')
        if (hashish and hashish != "None"):
            qrcode = Invoices.all()
            qrcode.filter("checksum", hashish)
            qr = qrcode.fetch(1)
            output = qr[0].qrlink
            if check:
                output = qr[0].qrchecksum
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(output)
        else:
            self.redirect('/images/noqrcode.png')

application = webapp.WSGIApplication([
                                      ('/', MainPage),
                                      ('/client', ClientHandler),
                                      ('/dashboard', DashboardHandler),
                                      ('/projects', ProjectsHandler),
                                      ('/addtime', AddTimesHandler),
                                      ('/timesheet', TimesheetHandler),
                                      ('/invoice', InvoiceHandler),
                                      ('/invoices', InvoicesHandler),
                                      ('/invoice-gen', InvoiceGenerateHandler),
                                      ('/project', ProjectHandler),
                                      ('/qr', GetQRLinkHandler),
                                      ('/service', ServiceHandler)
                                     ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
