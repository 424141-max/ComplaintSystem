from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Complaint, Crew


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('password1', 'password2'):
            previous_attrs = self.fields[field_name].widget.attrs
            self.fields[field_name].widget = forms.TextInput(attrs={
                **previous_attrs,
                'autocomplete': 'new-password',
            })

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ('category', 'description', 'location')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class StaffComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ('priority', 'status', 'assigned_crew')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        available_crews = Crew.objects.filter(is_available=True)
        if self.instance.assigned_crew_id:
            available_crews = Crew.objects.filter(
                Q(is_available=True) | Q(pk=self.instance.assigned_crew_id)
            )
        self.fields['assigned_crew'].queryset = available_crews

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('status') == Complaint.Status.CLOSED
            and not self.instance.completion_proof
        ):
            raise forms.ValidationError(
                'A crew must upload completion proof before this complaint can be closed.'
            )
        return cleaned_data