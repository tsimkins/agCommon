request = container.REQUEST
response =  request.response

return context.REQUEST.RESPONSE.redirect("%s/enablePublication" % context.absolute_url())
