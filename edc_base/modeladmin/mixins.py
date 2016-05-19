import re

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils import timezone
from django.utils.html import format_html


class ModelAdminBasicMixin(object):

    """Merge ModelAdmin attributes with the concrete class attributes fields, radio_fields, list_display,
    list_filter and search_fields.

    `mixin_exclude_fields` is a list of fields included in the mixin but not wanted on the concrete.

    Use for a ModelAdmin mixin prepared for an abstract models, e.g. edc_consent.models.BaseConsent."""

    mixin_fields = []

    mixin_radio_fields = {}

    mixin_list_display = []

    mixin_list_filter = []

    mixin_search_fields = []

    mixin_exclude_fields = []

    def get_list_display(self, request):
        self.list_display = list(super(ModelAdminBasicMixin, self).get_list_display(request) or [])
        self.list_display = self.extend_from(self.list_display, self.mixin_list_display)
        self.list_display = self.remove_from(self.list_display)
        return tuple(self.list_display)

    def get_list_filter(self, request):
        self.list_filter = list(super(ModelAdminBasicMixin, self).get_list_filter(request) or [])
        self.list_filter = self.update_from_mixin(self.list_filter, self.mixin_list_filter)
        return tuple(self.list_filter)

    def get_search_fields(self, request):
        self.search_fields = list(super(ModelAdminBasicMixin, self).get_search_fields(request) or [])
        self.search_fields = self.update_from_mixin(self.search_fields, self.mixin_search_fields)
        return tuple(self.search_fields)

    def get_fields(self, request, obj=None):
        self.radio_fields = self.get_radio_fields(request, obj)
        if self.mixin_fields:
            self.fields = self.update_from_mixin(self.fields, self.mixin_fields)
            return self.fields
        elif self.fields:
            return self.fields
        form = self.get_form(request, obj, fields=None)
        return list(form.base_fields) + list(self.get_readonly_fields(request, obj))

    def update_from_mixin(self, field_list, mixin_field_list):
        field_list = self.extend_from(field_list, mixin_field_list)
        field_list = self.remove_from(field_list)
        return tuple(field_list)

    def extend_from(self, field_list, mixin_field_list):
        return list(field_list) + list([fld for fld in mixin_field_list if fld not in field_list])

    def remove_from(self, field_list):
        field_list = list(field_list)
        for field in self.mixin_exclude_fields:
            try:
                field_list.remove(field)
            except ValueError:
                pass
        return tuple(field_list)

    def get_radio_fields(self, request, obj=None):
        self.radio_fields.update(self.mixin_radio_fields)
        for key in self.mixin_exclude_fields:
            try:
                del self.mixin_radio_fields[key]
            except KeyError:
                pass
        return self.radio_fields


class ModelAdminRedirectMixin(object):

    """Redirect on add, change, or delete."""

    def redirect_url(self, request, obj, post_url_continue=None):
        return None

    def redirect_url_on_add(self, request, obj, post_url_continue=None):
        return self.redirect_url(request, obj, post_url_continue)

    def redirect_url_on_change(self, request, obj, post_url_continue=None):
        return self.redirect_url(request, obj, post_url_continue)

    def redirect_url_on_delete(self, request, obj_display, obj_id):
        return None

    def response_add(self, request, obj, post_url_continue=None):
        redirect_url = None
        if '_addanother' not in request.POST and '_continue' not in request.POST:
            redirect_url = self.redirect_url_on_add(request, obj)
        if redirect_url:
            return HttpResponseRedirect(redirect_url)
        return super(ModelAdminRedirectMixin, self).response_add(request, obj)

    def response_change(self, request, obj, post_url_continue=None):
        redirect_url = None
        if '_addanother' not in request.POST and '_continue' not in request.POST:
            redirect_url = self.redirect_url_on_change(request, obj)
        if redirect_url:
            return HttpResponseRedirect(redirect_url)
        return super(ModelAdminRedirectMixin, self).response_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        redirect_url = self.redirect_url_on_delete(request, obj_display, obj_id)
        if redirect_url:
            return HttpResponseRedirect(redirect_url)
        return super(ModelAdminRedirectMixin, self).response_delete(request, obj_display, obj_id)


class ModelAdminNextUrlRedirectMixin(ModelAdminRedirectMixin):

    """Redirect to a named url in the querystring for a model add, change, delete."""

    redirect_url_get_attr = 'next_url'

    def redirect_url(self, request, obj, post_url_continue=None):
        redirect_url = super(ModelAdminNextUrlRedirectMixin, self).redirect_url(
            request, obj, post_url_continue)
        if request.GET.get(self.querystring_name):
            url_name = request.GET.get(self.querystring_name)
            return reverse(url_name)
        return redirect_url


class ModelAdminModelRedirectMixin(ModelAdminRedirectMixin):

    """Redirect to another model's changelist on add, change or delete."""

    redirect_app_label = None
    redirect_model_name = None
    redirect_search_field = None

    def search_value(self, obj):
        def objattr(inst):
            my_inst = inst
            for name in self.redirect_search_field.split('.'):
                my_inst = getattr(my_inst, name)
            return my_inst
        try:
            value = objattr(obj)
        except TypeError:
            value = None
        return value

    def redirect_url(self, request, obj, post_url_continue=None, namespace=None):
        namespace = namespace or 'admin'
        return '{}?q={}'.format(
            reverse(
                '{namespace}:{app_label}_{model_name}_changelist'.format(
                    namespace=namespace, app_label=self.redirect_app_label, model_name=self.redirect_model_name)),
            self.search_value(obj) or '')

    def redirect_url_on_delete(self, request, obj_display, obj_id, namespace=None):
        namespace = namespace or 'admin'
        return reverse(
            '{namespace}:{app_label}_{model_name}_changelist'.format(
                namespace=namespace, app_label=self.redirect_app_label, model_name=self.redirect_model_name))


class ModelAdminChangelistModelButtonMixin(object):

    """Use a button as a list_display field with a link to add, change or changelist"""

    changelist_model_button_template = '<a href="{{url}}" class="button" title="{title}" {disabled}>{label}</a>'

    def button_template(self, label, disabled=None, title=None, url=None):
        title = title or ''
        disabled = 'disabled' if disabled else ''
        if disabled or not url:
            url = '#'
        button_template = format_html(
            self.changelist_model_button_template, disabled=disabled, label=label, title=title)
        button_template = format_html(button_template, url=url)
        return button_template

    def changelist_model_button(self, app_label, model_name, reverse_args=None, change_label=None,
                                add_label=None, add_querystring=None, disabled=None, title=None):
        if disabled:
            changelist_model_button = self.disabled_button(add_label or change_label)
        else:
            app_label = app_label
            model_name = model_name
            if reverse_args:
                changelist_model_button = self.change_button(
                    app_label, model_name, reverse_args, label=change_label, title=title)
            else:
                changelist_model_button = self.add_button(app_label, model_name, add_label, add_querystring, title=title)
        return changelist_model_button

    def change_button(self, app_label, model_name, reverse_args, label=None, namespace=None, title=None):
        label = label or 'change'
        namespace = namespace or 'admin'
        url = reverse(
            '{namespace}:{app_label}_{model_name}_change'.format(
                namespace=namespace, app_label=app_label, model_name=model_name), args=reverse_args)
        return self.button_template(label, url=url, title=title)

    def add_button(self, app_label, model_name, label=None, querystring=None, namespace=None, title=None):
        label = label or 'add'
        namespace = namespace or 'admin'
        url = reverse(
            '{namespace}:{app_label}_{model_name}_add'.format(
                namespace=namespace, app_label=app_label, model_name=model_name)) + (querystring or '')
        return self.button_template(label, url=url, title=title)

    def changelist_list_button(self, app_label, model_name, querystring_value=None,
                               label=None, disabled=None, namespace=None, title=None):
        """Return a button that goes to the app changelist filter for this model instance."""
        label = label or 'change'
        namespace = namespace or 'admin'
        querystring = ''
        if querystring_value:
            querystring = '?q={}'.format(querystring_value)
        url = reverse(
            '{namespace}:{app_label}_{model_name}_changelist'.format(
                namespace=namespace, app_label=app_label, model_name=model_name)) + querystring
        return self.button_template(label, disabled=disabled, title=title, url=url)

    def disabled_button(self, label):
        return self.button_template(label, disabled='disabled', url='#')


class ModelAdminFormInstructionsMixin(object):
    """Add instructions to the add view context.

    Override the change_form.html to add {{ instructions }}

    Create a blank change_form.html in your /templates/admin/<app_label> folder
    and add this (or something like it):

        {% extends "admin/change_form.html" %}
        {% block field_sets %}
        {% if instructions %}
            <p class="help"><b>Instructions:</b>&nbsp;{{ instructions }}</p>
        {% endif %}
        {% if additional_instructions %}
            <p class="help"><b>Additional Instructions:</b>&nbsp;{{ additional_instructions }}</p>
        {% endif %}
        {{ block.super }}
        {% endblock %}

    """

    instructions = (
        'Please complete the form below. '
        'Required questions are in bold. '
        'When all required questions are complete click SAVE '
        'or, if available, SAVE NEXT. Based on your responses, additional questions may be '
        'required or some answers may need to be corrected.')

    additional_instructions = None

    add_additional_instructions = None
    add_instructions = None

    change_additional_instructions = None
    change_instructions = None

    def update_add_instructions(self, extra_context):
        extra_context = extra_context or {}
        extra_context['instructions'] = self.add_instructions or self.instructions
        extra_context['additional_instructions'] = (
            self.add_additional_instructions or self.additional_instructions)
        return extra_context

    def update_change_instructions(self, extra_context):
        extra_context = extra_context or {}
        extra_context['instructions'] = self.change_instructions or self.instructions
        extra_context['additional_instructions'] = (
            self.change_additional_instructions or self.additional_instructions)
        return extra_context

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = self.update_add_instructions(extra_context)
        print(extra_context)
        print(self.instructions)
        return super(ModelAdminFormInstructionsMixin, self).add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = self.update_change_instructions(extra_context)
        return super(ModelAdminFormInstructionsMixin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)


class ModelAdminAuditFieldsMixin(object):

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user_created = request.user.username
            obj.created = timezone.now()
        else:
            obj.user_modified = request.user.username
            obj.modified = timezone.now()
        super(ModelAdminAuditFieldsMixin, self).save_model(request, obj, form, change)

    def get_list_filter(self, request):
        columns = ['created', 'modified', 'user_created', 'user_modified', 'hostname_created']
        self.list_filter = list(self.list_filter or [])
        self.list_filter = self.list_filter + [item for item in columns if item not in self.list_filter]
        return tuple(self.list_filter)


class ModelAdminFormAutoNumberMixin(object):

    def auto_number(self, form):
        WIDGET = 1
        auto_number = True
        if 'auto_number' in dir(form._meta):
            auto_number = form._meta.auto_number
        if auto_number:
            for index, fld in enumerate(form.base_fields.items()):
                if not re.match(r'^\d+\.', str(fld[WIDGET].label)):
                    fld[WIDGET].label = '{0}. {1}'.format(str(index + 1), str(fld[WIDGET].label))
        return form

    def get_form(self, request, obj=None, **kwargs):
        form = super(ModelAdminFormAutoNumberMixin, self).get_form(request, obj, **kwargs)
        form = self.auto_number(form)
        return form
