
#             try:
#               import StringIO
#               data = "This is an invoice bitches!"
#               gconnect = Gconnection()
#               client = gconnect.docs_connect()
#               title = "Invoice #"
#               ms = gdata.MediaSource(file_handle=StringIO.StringIO(data), content_type="application/rtf", content_length=len(data))
#               entry = gdata.docs.service.DocsService()
#               foobar = entry._UploadFile(ms,title,gdata.docs.service.DOCUMENT_LABEL,'/feeds/documents/private/full')
#             except gdata.service.RequestError, request_exception:
#               request_error = request_exception[0]
#               if request_error['status'] == 401 or request_error['status'] == 403:
#                   self.response.out.write("401 or 403")
#               else:
#                   raise
            
            # Google DOCS 'UPLOAD' this works, but just creates an empty file, no content
             invoice_name = "Invoice #" + str(iid)
             gconnect = Gconnection()
             client = gconnect.docs_connect()
             new_doc = client.Create(gdata.docs.data.DOCUMENT_LABEL, invoice_name)
             invoice_update.docslink = new_doc.title.text