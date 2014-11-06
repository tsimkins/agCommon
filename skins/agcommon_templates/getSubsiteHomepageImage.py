from Products.agCommon import getSubsiteHomepageImage

request = container.REQUEST
RESPONSE =  request.RESPONSE

RESPONSE.setHeader('Content-Type', 'application/x-javascript')
RESPONSE.setHeader('Cache-Control', 'max-age=3600, s-maxage=3600, public, must-revalidate, proxy-revalidate')

print getSubsiteHomepageImage(context)
return printed
