#!/usr/bin/python

from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParseError

import urllib2

def ldapPersonLookup(psu_id):
    
    url = "http://www.psu.edu/cgi-bin/ldap/ldap_query.cgi?uid=%s" % psu_id
    
    fields = ['psu_id', 'last_name', 'first_name', 'middle_name', 'suffix', 'email', 'office_address', 'city', 'state', 'zip', 'phone', 'job_title',]
    
    ldap = {}
    data = {'psu_id' : psu_id.lower()}
    
    for f in fields:
        if not data.get(f):
            data[f] = ''

    try:
        mySoup = BeautifulSoup(urllib2.urlopen(url))
    except HTMLParseError:
        raise HTMLParseError("Error Parsing LDAP for %s" % psu_id)
    else:
        
        if str(mySoup.prettify()).count("reformulate"):
            raise ValueError("Not found in LDAP %s" % psu_id)
        else:
            table = mySoup.find("table")
    
            for row in table.findAll("tr"):

                th = row.findAll("th")
                td = row.findAll("td")

                if len(th) == 1 and len(td) == 1:
            
                    label = th[0].contents[0].strip().replace(":", "")
            
                    value = "".join([str(x).strip().replace("<br />", "\n") for x in td[0].contents]).strip()
            
                    if label == "E-mail":
                        value = td[0].find("a").contents[0]
                    
                    if len(value.split("\n")) > 1:
                        value = value.split("\n")
                    
                    ldap[label] = value

            name_array = [x.title() for x in ldap['Name'].split()]
            
            if len(name_array) == 3:
                data['last_name'] = name_array[2]
                data['first_name'] = name_array[0]
                data['middle_name'] = name_array[1]
            elif len(name_array) == 2:
                data['last_name'] = name_array[1]
                data['first_name'] = name_array[0]
            else:
                data['last_name'] = name_array[0]

            try:
                data['email'] = ldap['E-mail']
            except KeyError:
                data['email'] = ""
            
            if ldap.get("Address", "").count('UNIVERSITY PARK'):
                data['office_address'] = ldap.get("Address")[0].title()
                data['city'] = "University Park"
                data['state'] = "PA"
                data['zip'] = "16802"
            else:
                data['office_address'] = " ".join(ldap.get("Address", "")).title()
            
            if data['office_address'].startswith("0"):
                data['office_address'] = data['office_address'].replace("0", "", 1)
            
            data['phone'] = "-".join(ldap.get('Telephone Number', "").replace('+1', '').split())
            data['job_title'] = ldap.get('Title', "").title()
        
    return data
