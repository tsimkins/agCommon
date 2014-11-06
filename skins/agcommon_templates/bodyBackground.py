from Products.agCommon import bodyBackground
from DateTime import DateTime

request = container.REQUEST
RESPONSE =  request.RESPONSE

RESPONSE.setHeader('Content-Type', 'image/png')
RESPONSE.setHeader('Cache-Control', 'max-age=86400, s-maxage=86400, public, must-revalidate, proxy-revalidate')

# From http://www.peterbe.com/plog/cache-control_or_expires
hours = 24
now = DateTime() 
then = now+int(hours/24.0)
RESPONSE.setHeader('Expires',then.rfc822()) 

modified = now-int(hours/24.0)
RESPONSE.setHeader('Last-Modified',modified.rfc822()) 

print bodyBackground(context, request)

return printed
