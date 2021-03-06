import datetime
from django.conf import settings as django_settings
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.safestring import mark_safe
from django.db.models.fields import BLANK_CHOICE_DASH
from django import forms
from web.forms import MagiForm, AutoForm, MagiFiltersForm, MagiFilter
from bang.django_translated import t
from bang import models

############################################################
# Accounts

class AccountForm(MagiForm):
    def clean_start_date(self):
        if 'start_date' in self.cleaned_data:
            if self.cleaned_data['start_date']:
                if self.cleaned_data['start_date'] < datetime.date(2017, 3, 16):
                    raise forms.ValidationError(_('The game didn\'t even exist at that time.'))
                if self.cleaned_data['start_date'] > datetime.date.today():
                    raise forms.ValidationError(_('This date cannot be in the future.'))
        return self.cleaned_data['start_date']

    class Meta:
        model = models.Account
        fields = ('level', 'start_date')
        optional_fields = ('level', 'start_date')

class FilterAccounts(MagiFiltersForm):
    search_fields = ['owner__username', 'owner__preferences__description', 'owner__preferences__location']
    search_fields_exact = ['owner__email']

    ordering_fields = [
        ('level', _('Level')),
        ('owner__username', t['Username']),
        ('creation', _('Join Date')),
        ('start_date', _('Start Date')),
    ]

    member_id = forms.ChoiceField(choices=BLANK_CHOICE_DASH + [(id, full_name) for (id, full_name, image) in getattr(django_settings, 'FAVORITE_CHARACTERS', [])], required=False, label=_('Favorite Member'))
    member_id_filter = MagiFilter(selectors=['owner__preferences__favorite_character{}'.format(i) for i in range(1, 4)])

    class Meta:
        model = models.Account
        fields = ('search', 'member_id',)

############################################################
# Member

class MemberForm(AutoForm):
    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        # Change labels for staff
        self.fields['square_image'].label = 'Small icon (for the map)'
        self.fields['square_image'].help_text = mark_safe('Example: <img src="https://i.bandori.party/u/i/m/1Toyama-Kasumi-D7Fpvu.png" height="40">')

    class Meta:
        model = models.Member
        fields = '__all__'
        save_owner_on_creation = True
        optional_fields = ('band', 'school', 'i_school_year', 'CV', 'romaji_CV', 'birthday', 'food_likes', 'food_dislikes', 'i_astrological_sign', 'hobbies', 'description')

class MemberFilterForm(MagiFiltersForm):
    search_fields = ['name', 'japanese_name', 'school', 'CV', 'romaji_CV', 'food_likes', 'food_dislikes', 'hobbies', 'description']

    ordering_fields = [
        ('_cache_total_fans', _('Popularity')),
        ('name', _('Name')),
        ('japanese_name', string_concat(_('Name'), ' (', t['Japanese'], ')')),
        ('birthday', _('Birthday')),
    ]

    school = forms.ChoiceField(choices=BLANK_CHOICE_DASH + [(s, s) for s in getattr(django_settings, 'SCHOOLS', [])], initial=None)

    class Meta:
        model = models.Member
        fields = ('search', 'i_band', 'school', 'i_school_year', 'i_astrological_sign')

############################################################
# Card

class CardForm(AutoForm):
    def __init__(self, *args, **kwargs):
        super(CardForm, self).__init__(*args, **kwargs)
        self.previous_member_id = None if self.is_creating else self.instance.member_id
        self.fields['skill_details'].label = 'Skill details'

    def save(self, commit=False):
        instance = super(CardForm, self).save(commit=False)
        if self.previous_member_id != instance.member_id:
            instance.update_cache_member()
        if commit:
            instance.save()
        return instance

    class Meta:
        model = models.Card
        fields = '__all__'
        save_owner_on_creation = True
        optional_fields = ('image_trained', 'art_trained', 'transparent_trained', 'skill_name', 'japanese_skill_name', 'skill_details', 'school', 'i_school_year', 'CV', 'romaji_CV', 'birthday', 'food_likes', 'food_dislikes', 'i_astrological_sign', 'hobbies', 'description', 'performance_trained', 'technique_trained', 'visual_trained')

class CardFilterForm(MagiFiltersForm):
    search_fields = ['_cache_member_name', '_cache_member_japanese_name', 'skill_name', 'japanese_skill_name']
    ordering_fields = [
        ('id', _('ID')),
        ('_cache_member_name', string_concat(_('Member'), ' - ', _('Name'))),
        ('_cache_member_japanese_name', string_concat(_('Member'), ' - ', _('Name'), ' (', t['Japanese'], ')')),
        ('i_rarity', _('Rarity')),
        ('i_attribute', _('Attribute')),
        ('performance_max', _('Performance')),
        ('performance_trained_max', string_concat(_('Performance'), ' (', _('Trained'), ')')),
        ('technique_max', _('Technique')),
        ('technique_trained_max', string_concat(_('Technique'), ' (', _('Trained'), ')')),
        ('visual_max', _('Visual')),
        ('visual_trained_max', string_concat(_('Visual'), ' (', _('Trained'), ')')),
        ('_overall_max', _('Overall')),
        ('_overall_trained_max', string_concat(_('Overall'), ' (', _('Trained'), ')')),
    ]

    def _trainable_to_queryset(form, queryset, request, value):
        if value == '2':
            return queryset.filter(i_rarity__in=models.TRAINABLE_RARITIES)
        elif value == '3':
            return queryset.exclude(i_rarity__in=models.TRAINABLE_RARITIES)
        return queryset

    trainable = forms.NullBooleanField(initial=None, required=False, label=_('Trainable'))
    trainable_filter = MagiFilter(to_queryset=_trainable_to_queryset)
    member_id = forms.ChoiceField(choices=BLANK_CHOICE_DASH + [(id, full_name) for (id, full_name, image) in getattr(django_settings, 'FAVORITE_CHARACTERS', [])], initial=None, label=_('Member'))
    member_band = forms.ChoiceField(choices=BLANK_CHOICE_DASH + models.BAND_CHOICES, initial=None, label=_('Band'))
    member_band_filter = MagiFilter(selector='member__i_band')

    class Meta:
        model = models.Card
        fields = ('search', 'member_id', 'member_band', 'i_rarity', 'i_attribute', 'trainable', 'i_skill_type', 'member_band', 'ordering', 'reverse_order')
