"""Built-in plugins for file categorisation and reporting."""

from .extension import ExtensionCategorisationPlugin
from .magic import MagicNumberCategorisationPlugin
from .mime import MimeTypeCategorisationPlugin
from .reporters import JSONReporterPlugin, RichReporterPlugin, SilentReporterPlugin

__all__ = [
    "ExtensionCategorisationPlugin",
    "MagicNumberCategorisationPlugin",
    "MimeTypeCategorisationPlugin",
    "JSONReporterPlugin",
    "RichReporterPlugin",
    "SilentReporterPlugin",
]
