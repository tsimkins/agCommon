from Products.agCommon import enablePublication

request = container.REQUEST
response =  request.response

enabled = enablePublication(context)

if enabled:
    return context.REQUEST.RESPONSE.redirect("%s/edit" % context.absolute_url())
else:
    print """<p>Publication behavior already enabled for <a href="%s">%s</a>.</p>""" % (context.absolute_url(), context.Title().strip())
    print "<p>Options:</p><ul>"
    print """<li><a href="%s/edit">Edit Publication</a></li>""" % context.absolute_url()
    print """<li><a href="%s/manage_interfaces">Remove</a> <strong>*PublicationExtender</strong> interfaces.</li>""" % context.absolute_url()
    print "</ul>"
    return printed


