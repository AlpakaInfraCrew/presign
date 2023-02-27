from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def get_top_nav(request):
    return [
        {
            "type": "link",
            "label": _("My Organizers"),
            "url": reverse(
                "control:user-organizers",
                kwargs={},
            ),
            "active": (request.resolved_path.url_name == "user-organizers"),
            "icon": "people",
        },
        {
            "type": "link",
            "label": _("My Events"),
            "url": reverse(
                "control:user-events",
                kwargs={},
            ),
            "active": (request.resolved_path.url_name == "user-events"),
            "icon": "calendar",
        },
        {
            "type": "link",
            "label": _("Questionnaires"),
            "url": reverse(
                "control:questionnaires",
                kwargs={},
            ),
            "active": (request.resolved_path.url_name == "questionnaires"),
            "icon": "card-list",
        },
    ]


def get_organizer_nav_items(request, organizer):
    return [
        {"type": "seperator"},
        {
            "type": "link",
            "label": organizer.name,
            "url": reverse(
                "control:organizer",
                kwargs={"organizer": organizer.slug},
            ),
            "active": (request.resolved_path.url_name == "organizer"),
            "icon": "people",
        },
        {
            "type": "link",
            "label": _("Settings"),
            "url": reverse(
                "control:organizer-settings",
                kwargs={"organizer": organizer.slug},
            ),
            "active": (request.resolved_path.url_name == "organizer-settings"),
            "icon": "gear",
        },
        {
            "type": "link",
            "label": _("Questionnaires"),
            "url": reverse(
                "control:questionnaire-list",
                kwargs={"organizer": organizer.slug},
            ),
            "active": (request.resolved_path.url_name == "questionnaire-list"),
            "icon": "card-list",
        },
        {
            "type": "link",
            "label": _("Events"),
            "url": reverse(
                "control:event-list",
                kwargs={"organizer": organizer.slug},
            ),
            "active": (request.resolved_path.url_name == "event-list"),
            "icon": "calendar",
        },
    ]


def get_nav_items(request):
    nav_items = get_top_nav(request)

    if hasattr(request, "organizer"):
        nav_items.extend(get_organizer_nav_items(request, organizer=request.organizer))

    if hasattr(request, "event"):
        nav_items.extend(
            [
                {"type": "seperator"},
                {
                    "type": "link",
                    "label": request.event.name,
                    "url": reverse(
                        "control:event",
                        kwargs={
                            "organizer": request.organizer.slug,
                            "event": request.event.slug,
                        },
                    ),
                    "active": (request.resolved_path.url_name == "event"),
                    "icon": "calendar",
                },
                {
                    "type": "link",
                    "label": _("Settings"),
                    "url": reverse(
                        "control:event-change",
                        kwargs={
                            "organizer": request.organizer.slug,
                            "event": request.event.slug,
                        },
                    ),
                    "active": (request.resolved_path.url_name == "event-change"),
                    "icon": "gear",
                },
                {
                    "type": "link",
                    "label": _("Participants"),
                    "url": reverse(
                        "control:participant-list",
                        kwargs={
                            "organizer": request.organizer.slug,
                            "event": request.event.slug,
                        },
                    ),
                    "active": (request.resolved_path.url_name == "participant-list"),
                    "icon": "person",
                },
            ]
        )

    return nav_items


def contextprocessor(request):
    if (
        not hasattr(request, "resolved_path")
        or "control" not in request.resolved_path.namespaces
    ):
        return {}

    return {"nav_items": get_nav_items(request), "additional_nav_items": []}
