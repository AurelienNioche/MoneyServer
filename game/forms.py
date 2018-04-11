from django import forms


class ParametersForm(forms.Form):

    class Meta:
        abstract = True

    user_id = forms.IntegerField(required=False)
    t = forms.IntegerField(required=False)
    good = forms.IntegerField(required=False)
    sex = forms.CharField(required=False)
    age = forms.CharField(required=False)
    device_id = forms.CharField(required=False)
    demand = forms.CharField(required=True)


class ClientRequestForm(ParametersForm):

    def __init__(self, *args):

        super().__init__(*args)

        self.cleaned_data = None

    def clean(self):

        """
        called by is_valid method
        when the form is going
        to be validated
        """

        self.cleaned_data = super().clean()
