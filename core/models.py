import datetime
from decimal import Decimal

from django.contrib import admin
from django.core.validators import MinValueValidator
from django.db import models

# Create your models here.
from django.urls import reverse
from django.contrib.auth.models import AbstractUser  # Required to assign User as a borrower


class Situation(models.Model):
    situation = models.CharField(max_length=200)
    yearly_subscription_price = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.situation


class User(AbstractUser):
    # ban for two years if to many overdue items
    situation = models.ForeignKey(Situation, null=True, on_delete=models.SET_NULL)
    banned_until = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        return reverse('author-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Genre(models.Model):
    """Model representing a genre"""
    name = models.CharField(max_length=200, help_text='Enter a genre')

    def __str__(self):
        return self.name


class Item(models.Model):
    """
        Item is the base class for all types of items (Books, DVDs and CDs). it regroups all the common fields.
        type specific fields are defined in derived classes (Book, CD, DVD)
    """
    # types will stay relativaly the same, no need to create a separate Model, using choices is enough
    book, dvd, cd = "book", "dvd", "cd"
    TYPES_CHOICES = [
        (book, 'Book'),
        (dvd, 'DVD'),
        (cd, 'CD'),
    ]

    """ Model representing an item (but not a specific copy) """
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=200, choices=TYPES_CHOICES, default=book)
    # may have several authors
    author = models.ManyToManyField(Author, blank=True)

    genre = models.ManyToManyField(Genre, help_text='Select a genre for this item')
    description = models.TextField(max_length=1000, help_text='description of the item')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Returns the url to access details for this item"""
        return reverse('item-detail', kwargs={'pk': self.pk})

    def get_instance_count(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return self.iteminstance_set.count()

    def get_genres(self):
        return ", ".join([g.__str__() for g in self.genre.all()])

    def get_authors(self):
        return ", ".join([g.__str__() for g in self.author.all()])

    get_instance_count.short_description = "n° of items"


class ItemInstance(models.Model):
    available, on_loan, unavailable = 'a', 'l', 'u'

    STATUS_CHOICES = (
        (unavailable, 'Unavailable'),
        (on_loan, 'On loan'),
        (available, 'Available'),
    )

    as_new, good, poor = "as_new", "good", "poor"
    CONDITIONS_CHOICES = (
        (as_new, "As new"),
        (good, "Good"),
        (poor, "Poor"),
    )

    """ Model representing a specific copy of an item"""
    item = models.ForeignKey(Item, on_delete=models.RESTRICT)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, blank=False, null=False, default=available,
                              help_text="item status")
    condition = models.CharField(max_length=100, choices=CONDITIONS_CHOICES, blank=True, null=True,
                                 help_text="Item condition")

    def get_verbose(self):
        """Returns the url to access details for this item"""
        return "aaa"

    class Meta:
        ordering = ['item']

    def __str__(self):
        return f" (copy id {self.id})"


def get_initial_return_date():
    return datetime.datetime.now() + datetime.timedelta(days=30)


class Borrowing(models.Model):
    """ Model Representing a borrowing of an item """
    borrower = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    item = models.ForeignKey(ItemInstance, null=True, on_delete=models.SET_NULL)
    due_date = models.DateTimeField(default=get_initial_return_date, help_text='Initially set to now + 30days')
    overdue_fee = models.DecimalField(max_digits=64, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    overdue_fee_payed = models.BooleanField(default=False)
    borrowed = models.DateTimeField(default=datetime.datetime.now)
    returned = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"due date : {self.due_date}"
