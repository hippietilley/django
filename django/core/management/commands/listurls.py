import re
from importlib import import_module

from django.contrib.admindocs.views import (
    extract_views_from_urlpatterns,
    simplify_regex,
)
from django.core.management.base import BaseCommand


def replace_simple_regex(value, offset):
    if value == "<var>":
        return "<arg:{}>".format(offset)
    else:
        just_value = value.strip("<").strip(">")
        return "<kwarg:{}>".format(just_value)


class Command(BaseCommand):
    help = """Displays a list of urls used in the project."""

    def add_arguments(self, parser):
        parser.add_argument(
            "subdirectory",
            nargs="?",
            help="Only list URLs from this subdirectory.",
        )

    def handle(self, **options):
        from django.conf import settings

        urlconf = import_module(settings.ROOT_URLCONF)
        all_urls = extract_views_from_urlpatterns(urlconf.urlpatterns)

        output = ""
        subdirectory = options["subdirectory"] or ""
        if not subdirectory.startswith("/"):
            subdirectory = "/" + subdirectory
        for url in all_urls:
            simple_url = simplify_regex(url[1])
            if subdirectory == simple_url[: len(subdirectory)]:
                uri = "URL: " + self.style.HTTP_REDIRECT(simple_url)

                viewfunc = url[0]
                viewname = "{}.{}".format(
                    viewfunc.__module__,
                    getattr(viewfunc, "__name__", viewfunc.__class__.__name__),
                )
                view = "View: " + self.style.HTTP_NOT_MODIFIED(viewname)

                try:
                    namespace_list = url[2]
                except IndexError:
                    namespace_list = []

                try:
                    name = url[3]
                except IndexError:
                    name = None

                namespace = ""
                if namespace_list:
                    for part in namespace_list:
                        namespace += part + ":"
                if name:
                    name = "Name: " + self.style.HTTP_INFO(namespace + name)
                arguments = None

                named_groups = re.compile(r"<\w+>").findall(simple_url)
                all_groups = (
                    replace_simple_regex(var, index)
                    for index, var in enumerate(named_groups, start=1)
                )
                if all_groups:
                    arguments = "Arguments: " + self.style.HTTP_INFO(
                        ", ".join(tuple(all_groups))
                    )
                linelength = "-" * 20

                lineparts = (uri, view, name, arguments, linelength + "\n")
                lines = "\n".join(part for part in lineparts if part is not None)
                output = output + "\n" + lines
        if len(output) <= 0:
            return f"There are no URLs following { subdirectory }."
        return output
