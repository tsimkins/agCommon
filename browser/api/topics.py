# Ripped directly from
# https://github.com/plone/plone.app.contenttypes/blob/master/plone/app/contenttypes/migration/topics.py
# so I can fix issues fo rmigration
# -*- coding: utf-8 -*-
""" Migrate Topic to DX-Collectons.

Note on Subtopics:
When a migration of Subtopics is needed, you can replace the default itemish
Collection with a folderish Collection by creating a new type folderish
type 'Collection' with the collection-behavior enabled. You can then use
the default migration to migrate Topics with Subtopics.
"""

from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.contentmigration.inplace import InplaceCMFFolderMigrator
from Products.contentmigration.inplace import InplaceCMFItemMigrator
from Products.contentmigration.walker import CustomQueryWalker
from plone.app.contenttypes.behaviors.collection import ICollection
from plone.app.contenttypes.upgrades import LISTING_VIEW_MAPPING
from plone.app.querystring.interfaces import IQuerystringRegistryReader
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IMutableUUID
from zope.component import getUtility
from zope.component import queryAdapter
from zope.dottedname.resolve import resolve

import logging

logger = logging.getLogger(__name__)
prefix = "plone.app.querystring"

INVALID_OPERATION = 'Invalid operation %s for criterion: %s'


# Converters
class CriterionConverter(object):

    # Hardcoding because they're valid
    valid_operations = []

    # Last part of the code for the dotted operation method,
    # e.g. 'string.contains'.
    operator_code = ''
    # alternative code, possibly used if the first code does not work.
    alt_operator_code = ''

    def get_query_value(self, value, index, criterion):
        # value may contain a query and some parameters, but in the
        # simple case it is simply a value.
        return value

    def get_operation(self, value, index, criterion):
        # Get dotted operation method.  This may depend on value.
        # if index == 'Subject':
        #
        #     return "%s.operation.%s" % (prefix, 'selection.any')
        return "%s.operation.%s" % (prefix, self.operator_code)

    def get_alt_operation(self, value, index, criterion):
        # Get dotted operation method.  This may depend on value.
        return "%s.operation.%s" % (prefix, self.alt_operator_code)

    def is_index_known(self, registry, index):
        # Is the index registered as criterion index?
        key = '%s.field.%s' % (prefix, index)
        try:
            registry.get(key)
        except KeyError:
            logger.error("Index %s is no criterion index. Registry gives "
                         "KeyError: %s", index, key)
            return False
        return True

    def is_index_enabled(self, registry, index):
        # Is the index enabled as criterion index?
        key = '%s.field.%s.enabled' % (prefix, index)
        index_data = registry.get(key)
        if index_data:
            return True
        logger.warn("Index %s is not enabled as criterion index. ", index)
        return False

    def switch_type_to_portal_type(self, value, criterion):
        # 'portal_type' is the object id of the FTI in portal_types.
        # 'Type' is the title of that object.
        # For example:
        # - portal_type 'Document' has Type 'Page'.
        # - portal_type 'Topic' has Type 'Collection (old)'.
        if isinstance(value, dict):
            values = value.get('query', [])
        else:
            values = value
        if not values:
            return value
        new_values = []
        ttool = getToolByName(criterion, 'portal_types')
        type_to_portal_type = {}
        portal_types = ttool.objectIds()
        for portal_type, Type in ttool.listTypeTitles().items():
            type_to_portal_type[Type] = portal_type
        for Type in values:
            portal_type = type_to_portal_type.get(Type)
            if not portal_type:
                if Type in portal_types:
                    portal_type = Type
                else:
                    logger.warn("Cannot switch Type %r to portal_type.", Type)
                    continue
            new_values.append(portal_type)
        if isinstance(value, dict):
            value['query'] = new_values
        else:
            value = new_values
        return value

    def is_operation_valid(self, registry, operation):
        # See if we're white-listed
        if operation in self.valid_operations:
            return True
        # Check that the operation exists.
        op_function_name = registry.get('%s.operation' % operation)
        if op_function_name is None:
            logger.error("Operation %r is not defined.", operation)
            return False
        try:
            resolve(op_function_name)
        except ImportError:
            logger.error("ImportError for operation %r: %s",
                         operation, op_function_name)
            return False
        return True

    def get_valid_operation(self, registry, index, value, criterion):
        key = '%s.field.%s.operations' % (prefix, index)

        try:
            operations = list(registry.get(key))
        except TypeError:
            operations = []

        # Hardcoding in some valid operations per class
        operations.extend(self.valid_operations)

        operation = self.get_operation(value, index, criterion)

        if operation not in operations:
            operation = self.get_alt_operation(value, index, criterion)
            if operation not in operations:
                return
        if self.is_operation_valid(registry, operation):
            return operation

    def add_to_formquery(self, formquery, index, operation, query_value):
        row = {'i': index,
               'o': operation}
        if query_value is not None:
            row['v'] = query_value
        formquery.append(row)

    def __call__(self, formquery, criterion, registry):
        criteria = criterion.getCriteriaItems()
        if not criteria:
            logger.warn("Ignoring empty criterion %s.", criterion)
            return
        for index, value in criteria:
            # Check if the index is known and enabled as criterion index.
            if index == 'Type':
                # Try to replace Type by portal_type
                index = 'portal_type'
                value = self.switch_type_to_portal_type(value, criterion)
            if not self.is_index_known(registry, index):
                logger.info("Index %s not known in registry.", index)
                continue
            self.is_index_enabled(registry, index)
            # TODO: what do we do when this is False?  Raise an
            # Exception?  Continue processing the index and value
            # anyway, now that a warning is logged?  Continue with the
            # next criteria item?

            # Get the operation method.
            operation = self.get_valid_operation(
                registry,
                index,
                value,
                criterion
            )
            if not operation:
                logger.error(INVALID_OPERATION % (operation, criterion))
                # TODO: raise an Exception?
                continue

            # Get the value that we will query for.
            query_value = self.get_query_value(value, index, criterion)

            # Add a row to the form query.
            self.add_to_formquery(formquery, index, operation, query_value)


class ATDateCriteriaConverter(CriterionConverter):
    """Handle date criteria.

    Note that there is also ATDateRangeCriterion, which is much
    simpler as it just has two dates.

    In our case we have these valid operations:

    ['plone.app.querystring.operation.date.lessThan',
     'plone.app.querystring.operation.date.largerThan',
     'plone.app.querystring.operation.date.between',
     'plone.app.querystring.operation.date.lessThanRelativeDate',
     'plone.app.querystring.operation.date.largerThanRelativeDate',
     'plone.app.querystring.operation.date.today',
     'plone.app.querystring.operation.date.beforeToday',
     'plone.app.querystring.operation.date.afterToday']

    This code is based on the getCriteriaItems method from
    Products/ATContentTypes/criteria/date.py.  We check the field
    values ourselves instead of translating the values back and forth.
    """

    def __call__(self, formquery, criterion, registry):  # noqa
        if criterion.value is None:
            logger.warn("Ignoring empty criterion %s.", criterion)
            return
        field = criterion.Field()
        value = criterion.Value()

        # Check if the index is known and enabled as criterion index.
        if not self.is_index_known(registry, field):
            return
        self.is_index_enabled(registry, field)

        # Negate the value for 'old' days
        if criterion.getDateRange() == '-':
            value = -value

        date = DateTime() + value

        # Get the possible operation methods.
        key = '%s.field.%s.operations' % (prefix, field)
        operations = registry.get(key)

        def add_row(operation, value=None):
            if operation not in operations:
                # TODO just ignore it?
                raise ValueError(INVALID_OPERATION % (operation, criterion))
            if not self.is_operation_valid(registry, operation):
                # TODO just ignore it?
                raise ValueError(INVALID_OPERATION % (operation, criterion))
            # Add a row to the form query.
            row = {'i': field,
                   'o': operation}
            if value is not None:
                row['v'] = value
            formquery.append(row)

        operation = criterion.getOperation()
        if operation == 'within_day':
            if date.isCurrentDay():
                new_operation = "%s.operation.date.today" % prefix
                add_row(new_operation)
                return
            date_range = (date.earliestTime(), date.latestTime())
            new_operation = "%s.operation.date.between" % prefix
            add_row(new_operation, date_range)
            return
        if operation == 'more':
            if value != 0:
                new_operation = ("{0}.operation.date."
                                 "largerThanRelativeDate".format(prefix))
                add_row(new_operation, value)
                return
            else:
                new_operation = "{0}.operation.date.afterToday".format(prefix)
                add_row(new_operation)
                return
        if operation == 'less':
            if value != 0:
                new_operation = ("{0}.operation.date."
                                 "lessThanRelativeDate".format(prefix))
                add_row(new_operation, value)
                return
            else:
                new_operation = "{0}.operation.date.beforeToday".format(prefix)
                add_row(new_operation)
                return


class ATSimpleStringCriterionConverter(CriterionConverter):
    operator_code = 'string.contains'
    # review_state could be a string criterion, but should become a selection.
    alt_operator_code = 'selection.is'


class ATCurrentAuthorCriterionConverter(CriterionConverter):
    operator_code = 'string.currentUser'


class ATSelectionCriterionConverter(CriterionConverter):
    operator_code = 'selection.is'
    # alt_operator_code = 'selection.any'

    valid_operations = [
        'plone.app.querystring.operation.selection.any',
    ]

    def get_operation(self, value, index, criterion):
        # Get dotted operation method.  This may depend on value.
        if index == 'Subject':
            if value['operator'] == 'and':
                suffix = 'all'
            else:
                suffix = 'any'
            return "%s.operation.selection.%s" % (prefix, suffix)
        else:
            return "%s.operation.%s" % (prefix, self.operator_code)

    def get_query_value(self, value, index, criterion):
        values = value['query']
        if value.get('operator') == 'and' and len(values) > 1 and \
                index != 'Subject':
            logger.warn("Cannot handle selection operator 'and'. Using 'or'. "
                        "%r", value)

        # Special handling for portal_type=Topic.
        if index == 'portal_type' and 'Topic' in values:
            values = list(values)
            values[values.index('Topic')] = 'Collection'
            values = tuple(values)
        return values


class ATListCriterionConverter(ATSelectionCriterionConverter):
    alt_operator_code = 'string.is'


class ATReferenceCriterionConverter(ATSelectionCriterionConverter):
    # Note: the new criterion is disabled by default.  Also, it
    # needs the _referenceIs function in the plone.app.querystring
    # queryparser and that function is not defined.
    operator_code = 'reference.is'


class ATPathCriterionConverter(CriterionConverter):
    operator_code = 'string.path'

    def get_query_value(self, value, index, criterion):
        raw = criterion.getRawValue()
        if not raw:
            return
        # Is this a recursive query?  Could check depth in the value
        # actually, but Recurse is the canonical way.  Also, the only
        # possible values for depth are -1 and 1.
        if not criterion.Recurse():
            for index, path in enumerate(raw):
                raw[index] = path + '::1'
        return raw

    def add_to_formquery(self, formquery, index, operation, query_value):
        if query_value is None:
            return
        for value in query_value:
            row = {'i': index,
                   'o': operation,
                   'v': value}
            formquery.append(row)


class ATBooleanCriterionConverter(CriterionConverter):

    def get_operation(self, value, index, criterion):
        # Get dotted operation method.
        # value is one of these beauties:
        # value = [1, True, '1', 'True']
        # value = [0, '', False, '0', 'False', None, (), [], {}, MV]
        if True in value:
            code = 'isTrue'
        elif False in value:
            code = 'isFalse'
        else:
            logger.warn("Unknown value for boolean criterion. "
                        "Falling back to True. %r", value)
            code = 'isTrue'
        return "%s.operation.boolean.%s" % (prefix, code)

    def __call__(self, formquery, criterion, registry):
        criteria = criterion.getCriteriaItems()
        if not criteria:
            return
        for index, value in criteria:
            if index == 'is_folderish':
                fieldname = 'isFolderish'
            elif index == 'is_default_page':
                fieldname = 'isDefaultPage'
            else:
                fieldname = index
            # Check if the index is known and enabled as criterion index.
            if not self.is_index_known(registry, fieldname):
                continue
            self.is_index_enabled(registry, fieldname)
            # Get the operation method.
            operation = self.get_valid_operation(
                registry, fieldname, value, criterion)
            if not operation:
                logger.error(INVALID_OPERATION % (operation, criterion))
                # TODO: raise an Exception?
                continue
            # Add a row to the form query.
            row = {'i': index,
                   'o': operation}
            formquery.append(row)


class ATDateRangeCriterionConverter(CriterionConverter):
    operator_code = 'date.between'

    def get_query_value(self, value, index, criterion):
        return value['query']


class ATPortalTypeCriterionConverter(CriterionConverter):
    operator_code = 'selection.any'
    alt_operator_code = 'selection.is'

    def get_query_value(self, value, index, criterion):
        # Special handling for portal_type=Topic.
        if 'Topic' in value:
            value = list(value)
            value[value.index('Topic')] = 'Collection'
            value = tuple(value)
        return value


class ATRelativePathCriterionConverter(CriterionConverter):
    # We also have path.isWithinRelative, but its function is not defined.
    operator_code = 'string.relativePath'

    def get_query_value(self, value, index, criterion):
        if not criterion.Recurse():
            logger.warn("Cannot handle non-recursive path search. "
                        "Allowing recursive search. %r", value)
        return criterion.getRelativePath()


class ATSimpleIntCriterionConverter(CriterionConverter):
    # Also available: int.lessThan, int.largerThan.
    operator_code = 'int.is'

    def get_operation(self, value, index, criterion):
        # Get dotted operation method.
        direction = value.get('range')
        if not direction:
            code = 'is'
        elif direction == 'min':
            code = 'largerThan'
        elif direction == 'max':
            code = 'lessThan'
        elif direction == 'min:max':
            logger.warn("min:max direction not supported for integers. %r",
                        value)
            return
        else:
            logger.warn("Unknown direction for integers. %r", value)
            return
        return "{0}.operation.int.{1}".format(prefix, code)

    def get_query_value(self, value, index, criterion):
        if isinstance(value['query'], tuple):
            logger.warn("More than one integer is not supported. %r", value)
            return
        return value['query']


CONVERTERS = {
    # Create an instance of each converter.
    'ATBooleanCriterion': ATBooleanCriterionConverter(),
    'ATCurrentAuthorCriterion': ATCurrentAuthorCriterionConverter(),
    'ATDateCriteria': ATDateCriteriaConverter(),
    'ATDateRangeCriterion': ATDateRangeCriterionConverter(),
    'ATListCriterion': ATListCriterionConverter(),
    'ATPathCriterion': ATPathCriterionConverter(),
    'ATPortalTypeCriterion': ATPortalTypeCriterionConverter(),
    'ATReferenceCriterion': ATReferenceCriterionConverter(),
    'ATRelativePathCriterion': ATRelativePathCriterionConverter(),
    'ATSelectionCriterion': ATSelectionCriterionConverter(),
    'ATSimpleIntCriterion': ATSimpleIntCriterionConverter(),
    'ATSimpleStringCriterion': ATSimpleStringCriterionConverter(),
}

def get_collection_critera(context, registry):

    _collection_sort_reversed = None
    _collection_sort_on = None
    _collection_query = None

    path = '/'.join(context.getPhysicalPath())

    # Get the old criteria.
    # See also Products.ATContentTypes.content.topic.buildQuery

    criteria = context.listCriteria()

    logger.debug("Old criteria for %s: %r", path,
                    [(crit, crit.getCriteriaItems()) for crit in criteria])

    formquery = []

    for criterion in criteria:
        type_ = criterion.__class__.__name__

        if type_ == 'ATSortCriterion':
            # Sort order and direction are now stored in the Collection.
            _collection_sort_reversed = criterion.getReversed()
            _collection_sort_on = criterion.Field()
            logger.debug("Sort on %r, reverse: %s.",
                            _collection_sort_on,
                            _collection_sort_reversed)
            continue

        converter = CONVERTERS.get(type_)
        if converter is None:
            msg = 'Unsupported criterion %s' % type_
            logger.error(msg)
            raise ValueError(msg)
        converter(formquery, criterion, registry)

    logger.debug("New query for %s: %r", path, formquery)

    return formquery
