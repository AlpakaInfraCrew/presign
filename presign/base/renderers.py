from django.template.loader import render_to_string

from django_bootstrap5.forms import render_form
from django_bootstrap5.renderers import FormsetRenderer


class CardFormsetRenderer(FormsetRenderer):
    def render_forms(self):
        rendered_forms = []
        kwargs = self.get_kwargs()
        kwargs.pop("layout")
        for form in self.formset.forms:
            rendered_forms.append(render_form(form, **kwargs))

        return render_to_string(
            "formset_renderers/card_formset_renderer.html",
            {"rendered_forms": rendered_forms},
        )
