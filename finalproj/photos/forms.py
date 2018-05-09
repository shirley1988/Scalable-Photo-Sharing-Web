from django import forms

class UserForm(forms.Form):
    firstname = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'placeholder':'First Name'}))
    lastname = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    auth = forms.CharField(widget=forms.PasswordInput(), max_length=64)
    auth_confirm = forms.CharField(widget=forms.PasswordInput(), max_length=64)

    def is_valid(self):
        if not super(UserForm, self).is_valid():
            return False
        data = self.cleaned_data
        return (8 <= len(data['auth']) <= 64) and (not " " in data['auth']) and (data['auth'] == data['auth_confirm'])

