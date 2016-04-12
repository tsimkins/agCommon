from agsci.w3c.content import getText
from BeautifulSoup import BeautifulSoup
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.agCommon import toISO
from collective.contentleadimage.utils import getImageAndCaptionFieldNames, getImageAndCaptionFields
import Missing
import json
import re
import urllib2
import urlparse

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

class BaseView(BrowserView):

    # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
    def format_key(self, name):
        s1 = first_cap_re.sub(r'\1_\2', name)
        return all_cap_re.sub(r'\1_\2', s1).lower()
    
    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    def html_to_text(self, html):
        portal_transforms = getToolByName(self.context, 'portal_transforms')
        text = portal_transforms.convert('html_to_text', html).getData()
        return text
        

    def getMetadata(self):
        m = self.portal_catalog.getMetadataForUID("/".join(self.context.getPhysicalPath()))
        for i in m.keys():
            if m[i] == Missing.Value:
                m[i] = ''
        return m

    def getIndexData(self):
        return self.portal_catalog.getIndexDataForUID("/".join(self.context.getPhysicalPath()))

    def getCatalogData(self):
        data = self.getMetadata()
        indexdata = self.getIndexData()
        for i in indexdata.keys():
            if not data.has_key(i):
                data[i] = indexdata[i]
        return data

    def getExcludeFields(self):
        return [
            'allowedRolesAndUsers',
            'author_name',
            'cmf_uid',
            'commentators',
            'Creator',
            'CreationDate',
            'Date',
            'EffectiveDate',
            'effectiveRange',
            'ExpirationDate',
            'getCommitteeNames',
            'getDepartmentNames',
            'getIcon',
            'getObjPositionInParent',
            'getObjSize',
            'getRawClassifications',
            'getRawCommittees',
            'getRawDepartments',
            'getRawPeople',
            'getRawRelatedItems',
            'getRawSpecialties',
            'getResearchTopics',
            'getSortableName',
            'getSpecialtyNames',
            'id',
            'in_reply_to',
            'in_response_to',
            'last_comment_date',
            'meta_type',
            'ModificationDate',
            'object_provides',
            'portal_type',
            'path',
            'SearchableText',
            'sortable_title',
            'total_comments',
        ]

    def filterData(self, data):

        excluded_fields = self.getExcludeFields()

        # First pass: Adjust data if necessary
        for i in data.keys():
            if i in excluded_fields or not data.get(i):
                del data[i]
                continue

            v = data[i]
            
            if isinstance(v, DateTime):
                data[i] = toISO(data[i])
            elif i == 'getClassificationNames':
                data['directory_classifications'] = data[i]
                del data[i]
            elif i == 'listCreators':
                data['creators'] = data[i]
                del data[i]

        # Second pass: Ensure keys are non-camel case lowercase                
        for i in data.keys():
            formatted_key = self.format_key(i)

            if formatted_key != i:
                data[formatted_key] = data[i]
                del data[i]

        return data

    def getBaseData(self):
        data = self.getCatalogData()

        # Object URL
        url = self.context.absolute_url()
        data['url'] = url
        
        if data.get('hasContentLeadImage', False):
            img_field = getImageAndCaptionFieldNames(self.context)[0]
            img_caption_field = getImageAndCaptionFields(self.context)[1]

            if img_field: 
                data['image_url'] = '%s/%s' % (data['url'], img_field)
                
            if img_caption_field:
                data['image_caption'] = img_caption_field.get(self.context)

        # Get the html and text of the content if the 'full' parameter is used
        if self.request.form.get('full', None):
            try:
                html = getText(self.context)
            except:
                pass
            else:    
                if html:
                    soup = BeautifulSoup(html)
                    
                    # Convert relative img src to full URL path
                    for img in soup.findAll('img'):
                        src = img.get('src')
                        if src and not src.startswith('http'):
                            img['src'] = urlparse.urljoin(url, src)
                    
                    data['html'] = repr(soup)
                    data['text'] = self.html_to_text(html).strip()

        return data
    
    def getData(self, recursive=True):
        return self.getBaseData()

    def getFilteredData(self, recursive=True):
        data = self.getData(recursive=recursive)
        return self.filterData(data)        

    def getJSON(self):
        return json.dumps(self.getFilteredData(), indent=4)
        
    def __call__(self):
        json = self.getJSON()
        self.request.response.setHeader('Content-Type', 'application/json')
        return json

def getAPIData(object_url):
        
    # Grab JSON data
    json_url = '%s/@@api-json' % object_url

    try:
        json_data = urllib2.urlopen(json_url).read()
    except urllib2.HTTPError:
        raise ValueError("Error accessing object, url: %s" % json_url)

    # Convert JSON to Python structure
    try:
        data = json.loads(json_data)
    except ValueError:
        raise ValueError("Error decoding json: %s" % json_url)

    return data