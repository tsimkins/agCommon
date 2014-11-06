from Products.agCommon import getPortletHomepageImage

request = container.REQUEST
RESPONSE =  request.RESPONSE

RESPONSE.setHeader('Content-Type', 'application/x-javascript')
RESPONSE.setHeader('Cache-Control', 'max-age=3600, s-maxage=3600, public, must-revalidate, proxy-revalidate')

print getPortletHomepageImage(context)
return printed