"""Experimental exact text extraction; use only in a bounded isolated worker.

Not installed in any sender. Caller must never treat a decode as delivery proof.
"""
import typedstream
from typedstream.archiving import GenericArchivedObject, TypedValue
from typedstream.types.foundation import NSString


def decode_text(blob):
    if type(blob) is not bytes or not blob or len(blob) > 262144:
        return None
    try:
        value = typedstream.unarchive_from_data(blob)
        if not isinstance(value, GenericArchivedObject):
            return None
        cls = value.clazz
        if cls.name == b'NSMutableAttributedString' and cls.version == 0:
            cls = cls.superclass
        if cls is None or cls.name != b'NSAttributedString' or cls.version != 0:
            return None
        parent = cls.superclass
        if parent is None or parent.name != b'NSObject' or parent.version != 0 or parent.superclass is not None:
            return None
        if not value.contents:
            return None
        field = value.contents[0]
        if not isinstance(field, TypedValue) or field.encoding != b'@' or not isinstance(field.value, NSString):
            return None
        text = field.value.value
        if type(text) is not str or len(text) > 20000:
            return None
        return text
    except Exception:
        # No raw archive contents or parser errors enter logs/receipts.
        return None
