from dataclasses import Field
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, HTML, ButtonHolder

def crispy_form(form, helper, submit_button_text='Submit'):
    helper.form_method = 'post'
    helper.form_action = ''  # Or the URL you want to submit to
    helper.layout = Layout(
        Field set(
            '',
            *form.visible_fields(),
        ),
        ButtonHolder(
            Submit('submit', submit_button_text, css_class='btn-primary'),
        )
    )
    return helper