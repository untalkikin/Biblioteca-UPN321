from django import template

register = template.Library()


@register.filter
def add_class(field, css):
    """Add a CSS class to a form field widget from a template.

    Uso en plantillas:
        {{ form.title|add_class:"form-control" }}

    Esto facilita la integración con frameworks CSS (Bootstrap, etc.).
    """
    return field.as_widget(attrs={"class": css})
