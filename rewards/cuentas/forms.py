from django.contrib.auth.forms import PasswordChangeForm


class CambiarPasswordForm(PasswordChangeForm):
    """Mismo PasswordChangeForm de Django, con clases de Bootstrap para que
    combine con el resto de los formularios del panel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
