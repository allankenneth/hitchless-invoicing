#!/usr/bin/env python
import gdata.docs.client
import gdata.docs.data
import gdata.docs.service
import gdata.contacts
import gdata.calendar
import gdata.calendar.service
import gdata.service
import gdata.auth
import settings

class Gconnection():
    def contacts_connect(self):
        gd_client = gdata.contacts.service.ContactsService()
        gd_client.email = settings.CONTACTS["email"]
        gd_client.password = settings.CONTACTS["pass"]
        gd_client.source = settings.APP["gaename"]
        gd_client.ProgrammaticLogin()
        return gd_client
    def calendar_connect(self):
        gd_client = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(gd_client)
        gd_client.email = settings.CAL["email"]
        gd_client.password = settings.CAL["pass"]
        gd_client.source = settings.APP["gaename"]
        gd_client.ProgrammaticLogin()    
        return gd_client
    def docs_connect(self):
        gd_client = gdata.docs.client.DocsClient()
        gd_client.ClientLogin(settings.DOCS["email"], settings.DOCS["pass"], settings.APP["gaename"]);
        return gd_client
    def contacts(self):
        clients = list()
        gconnect = Gconnection()
        contacts_query = gconnect.contacts_connect()
        query = gdata.contacts.service.ContactsQuery()
        query['sortorder'] = 'descending'
        query.orderby = 'lastmodified'
        query['group'] = settings.CONTACTS["groupurl"]
        feed = contacts_query.GetContactsFeed(query.ToUri())
        for i, entry in enumerate(feed.entry):
          company = entry.organization.org_name.text
          name = entry.title.text
          title = entry.organization.org_title.text
          for email in entry.email:
            if email.primary and email.primary == 'true':
              email_address = email.address
          if entry.content:
            notes = entry.content.text
          else:
            notes = 'No notes.'
          value = entry.extended_property
          info = [company, name, title, email_address, notes, value]
          clients.append(info)
        return clients
    def groups(self):
        groups = list()
        gconnect = Gconnection()
        groups_query = gconnect.contacts_connect()
        feed = groups_query.GetGroupsFeed()
        for i, entry in enumerate(feed.entry):
          nextgroup = [entry.title.text,entry.id.text]
          groups.append(nextgroup)
        return groups