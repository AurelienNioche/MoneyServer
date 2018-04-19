from django import forms

from crispy_forms.bootstrap import Field, Accordion, AccordionGroup
from crispy_forms.helper import FormHelper


class ParametersForm(forms.Form):

    class Meta:
        abstract = True

    t_max = forms.IntegerField(
        label="Duration",
        required=True,
        initial=20,
    )

    tutorial_t_max = forms.IntegerField(
        label="Tutorial Duration",
        required=True,
        initial=5,
    )


class RoomForm(ParametersForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args)

        self.n_type = None

        self.generate_types(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.group = (Field(field) for field in self.fields)

        self.helper.layout = Accordion(
            AccordionGroup('Parameters', *self.group),
        )

        self.cleaned_data = None

    def generate_types(self, *args, **kwargs):

        if kwargs.get("n_type"):

            for i in range(int(kwargs["n_type"])):

                self.fields[f"x{i}"] = forms.IntegerField(
                    required=True,
                    label=f"x{i}",
                    initial=1
                )
        else:

            request = args[0]

            self.n_type = self.count_n_type(request)

            for i in range(self.n_type):

                self.fields[f"x{i}"] = forms.IntegerField(
                    required=True,
                    label=f"x{i}",
                    initial=1
                )

    def clean(self):

        """
        called by is_valid method
        when the form is going
        to be validated
        """

        self.cleaned_data = super().clean()

        self.cleaned_data["n_good"] = self.n_type

    def get_data(self):

        return self.cleaned_data

    @staticmethod
    def count_n_type(dic):
        return len([k for k in dic.keys() if k.startswith("x")])
