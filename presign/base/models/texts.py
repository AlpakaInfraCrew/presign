from hierarkey.models import GlobalSettingsBase, Hierarkey
from i18nfield.strings import LazyI18nString

from .participant import ParticipantStateActions, ParticipantStates

email_hierarkey = Hierarkey(attribute_name="email_texts")
status_hierarkey = Hierarkey(attribute_name="status_texts")


class TextMixin:
    def get_action_email_texts(self, action: "ParticipantStateActions"):
        action_texts = self.email_texts.get(action, as_type=dict, default="{}")
        return {
            "subject": LazyI18nString(action_texts.get("subject", {})),
            "body": LazyI18nString(action_texts.get("body", {})),
        }

    def get_status_text(self, status: "ParticipantStates"):
        status_text = self.status_texts.get(status, as_type=dict, default="{}")
        return LazyI18nString(status_text)


@email_hierarkey.set_global()
@status_hierarkey.set_global()
class GlobalSettings(GlobalSettingsBase):
    pass
