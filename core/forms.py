from django.core.exceptions import ValidationError
from django.forms import ModelForm, widgets
from core.models import ItemInstance, Borrowing, User, Item
from core.validators import validate_loan


class ItemInstanceForm(ModelForm):
    class Meta:
        model = ItemInstance
        fields = ['condition']

class BorrowingForm(ModelForm):
    """
    uses orm to populate modelchoicefield, but the sql query is :
    "SELECT * FROM {User._meta.db_table}"
    """

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['item'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        borrower = cleaned_data.get("borrower")
        iteminstance = cleaned_data.get("item")

        validate_loan(borrower, iteminstance)

    class Meta:
        model = Borrowing
        exclude = ['borrowed', 'overdue_fee', 'overdue_fee_payed', 'returned']
        widgets = {
            'due_date': widgets.DateTimeInput(attrs={'type': 'datetime'}),
            'returned': widgets.DateTimeInput(attrs={'type': 'date'}),
        }


class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = '__all__'





