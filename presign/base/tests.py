from django.template import Context, Template

from pytest_django.asserts import assertHTMLEqual


def test_markdownify():
    template = Template("{% load presign_tags %}\n{{ body | markdownify }}")
    context = Context({"body": "**Test** String"})
    rendered = template.render(context)
    assertHTMLEqual(rendered, "<p><strong>Test</strong> String</p>")

    context = Context({"body": "**Test** <script>alert()</script>String"})
    rendered = template.render(context)
    assertHTMLEqual(rendered, "<p><strong>Test</strong> String</p>")
