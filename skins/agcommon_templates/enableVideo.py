from Products.agCommon import unprotectRequest, enableVideoPage

unprotectRequest(container.REQUEST)

request = container.REQUEST
response =  request.response

enabled = enableVideoPage(context)

if enabled:
    return context.REQUEST.RESPONSE.redirect("%s/edit" % context.absolute_url())
else:
    print """<p>Video behavior already enabled for <a href="%s">%s</a>.</p>""" % (context.absolute_url(), context.Title().strip())
    print "<p>Options:</p><ul>"
    print """<li><a href="%s/edit">Edit Page</a></li>""" % context.absolute_url()
    print """<li><a href="%s/manage_interfaces">Remove</a> <strong>IVideoPage</strong> interface.</li>""" % context.absolute_url()
    print "</ul>"
    return printed


