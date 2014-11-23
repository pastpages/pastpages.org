from django.utils import six
from django.utils.six import StringIO
from django.shortcuts import get_object_or_404
from django.utils.timezone import is_naive
from django.utils import tzinfo
from django.templatetags.tz import utc
from django.utils.feedgenerator import rfc3339_date
from django.contrib.syndication.views import Feed, add_domain
from django.contrib.sites.models import get_current_site
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.encoding import iri_to_uri
from django.core.exceptions import ImproperlyConfigured
from .feedgenerator import TimemapLinkFeedGenerator


class TimemapLinkList(Feed):
    """
    An feed class that returns a list in Memento's Timemap format.
    """
    feed_type = TimemapLinkFeedGenerator

    def item_datetime(self, item):
        raise ImproperlyConfigured('Define an item_datetime() method in \
your %s class.' % self.__class__.__name__)

    def __get_dynamic_attr(self, attname, obj, default=None):
        try:
            attr = getattr(self, attname)
        except AttributeError:
            return default
        if callable(attr):
            # Check co_argcount rather than try/excepting the function and
            # catching the TypeError, because something inside the function
            # may raise the TypeError. This technique is more accurate.
            try:
                code = six.get_function_code(attr)
            except AttributeError:
                code = six.get_function_code(attr.__call__)
            if code.co_argcount == 2:       # one argument is 'self'
                return attr(obj)
            else:
                return attr()
        return attr

    def get_feed(self, obj, request):
        """
        Returns a feedgenerator.DefaultFeed object, fully populated, for
        this feed. Raises FeedDoesNotExist for invalid parameters.
        """
        current_site = get_current_site(request)
        feed = self.feed_type(
            original_url = self.get_original_url(obj),
            timemap_url = add_domain(
                current_site.domain,
                request.path,
                request.is_secure(),
            ),
        )
        for item in self.__get_dynamic_attr('items', obj):
            link = add_domain(
                current_site.domain,
                self.__get_dynamic_attr('item_link', item),
                request.is_secure(),
            )
            item_datetime = self.__get_dynamic_attr('item_datetime', item)
            if item_datetime and is_naive(item_datetime):
                item_datetime = utc(item_datetime)
            feed.add_item(
                link = link,
                datetime = item_datetime,
            )
        return feed