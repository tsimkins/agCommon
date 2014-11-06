# This script will trawl through all the Plone sites at the root level of the site, and 
# update the base_properties file to contain any new base_properties
#
# No more "white screen of death"

for myKey in context.keys():
	
	myChild = getattr(context, myKey)
	
	try:
		if myChild.getPortalTypeName() == 'Plone Site':

			try:
				# Let's give it a go!
				print "Updating %s" % (myChild['id'])
				portal_skins = getattr(myChild, 'portal_skins')

				custom = getattr(portal_skins, 'custom')

				try:
					agcommon_styles = getattr(portal_skins, 'agcommon_styles')
				except:
					print "ERROR: %s : agCommon skin not installed" % myKey
					continue
					
				try:
					custom_base_properties = getattr(custom, 'base_properties')
				except:
					print "ERROR: %s : No customized base_properties" % myKey
					continue
					
				base_properties = getattr(agcommon_styles, 'base_properties')

				try:			
					for myProperty in base_properties.propertyItems():
						(myPropertyKey, myPropertyValue) = myProperty
			
						if not custom_base_properties.getProperty(myPropertyKey):
							myPropertyType = base_properties.getPropertyType(myPropertyKey)
							try:
								custom_base_properties.manage_addProperty(myPropertyKey, myPropertyValue, myPropertyType)
							except:
								print "ERROR: %s : Error adding property %s:%s=%s" % (myKey, myPropertyKey, myPropertyType, myPropertyValue)
								continue
								
							print "Added %s:%s=%s" % (myPropertyKey, myPropertyType, myPropertyValue)
				except:
					print "ERROR: %s : Problem updating properties" % myKey
			except:
				print "ERROR: %s : Some other error" % myKey
	except:
		# No portal type name
		# print "ERROR: %s : No Portal Type Name" % myKey
		pass				


		
return printed