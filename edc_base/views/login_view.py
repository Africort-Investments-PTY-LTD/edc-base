from braces.views import FormInvalidMessageMixin
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import FormView

from edc_base.form.forms import LoginForm

from .edc_base_view_mixin import EdcBaseViewMixin


class LoginView(FormInvalidMessageMixin, EdcBaseViewMixin, FormView):
    template_name = "edc_base/login.html"
    form_class = LoginForm
    success_url = '/home/'
    form_invalid_message = 'Invalid username or password.'

    def get(self, request, *args, **kwargs):
        logout(request)
        return FormView.get(self, request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return self.request.GET.get('next', self.success_url)

    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password'))
        if user:
            if user.is_active:
                login(self.request, user)
                return super(FormView, self).form_valid(form)
        return self.form_invalid(form)
