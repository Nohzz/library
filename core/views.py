import datetime

from django.db import connections
from django.db.models import prefetch_related_objects
from django.forms import model_to_dict
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic import CreateView, DeleteView, UpdateView

from sqlhelpers import get_object_by_pk, save_object_to_db, delete_object, update_iteminstance_status, \
    update_borrowing_due_date, update_borrowing_returned
from .forms import ItemInstanceForm, BorrowingForm, ItemForm
from .models import Item, ItemInstance, Author, Genre, Borrowing, User, Situation

# Create your views here.
from .update import update_fees_and_bans


def ItemDetailView(request, pk):
    active_borrowing_id = {}

    # Select the item (using raw SQL with helper function)
    item = get_object_by_pk(Item, pk)

    # fetch the authors (id and name)
    authors = Author.objects.raw(f"""
    SELECT (`core_item_author`.`item_id`) AS `_prefetch_related_val_item_id`,
       `core_author`.`id`,
       `core_author`.`first_name`,
       `core_author`.`last_name`
    FROM `core_author`
    INNER JOIN `core_item_author`
    ON (`core_author`.`id` = `core_item_author`.`author_id`)
    WHERE `core_item_author`.`item_id` IN ({pk})
    ORDER BY `core_author`.`last_name` ASC,
          `core_author`.`first_name` ASC""")

    # fetch genres

    genres = Genre.objects.raw(f"""
    SELECT (`core_item_genre`.`item_id`) AS `_prefetch_related_val_item_id`,
   `core_genre`.`id`,
   `core_genre`.`name`
    FROM `core_genre`
    INNER JOIN `core_item_genre`
    ON (`core_genre`.`id` = `core_item_genre`.`genre_id`)
    WHERE `core_item_genre`.`item_id` IN ({pk})
    """)

    # Select the item instances
    item_instances = ItemInstance.objects.raw(f"""
    SELECT `core_iteminstance`.`id`,
   `core_iteminstance`.`item_id`,
   `core_iteminstance`.`status`,
   `core_iteminstance`.`condition`
    FROM `core_iteminstance`
    WHERE `core_iteminstance`.`item_id` IN ({pk})
    ORDER BY `core_iteminstance`.`item_id` ASC
    """)

    n_instances = item_instances.__len__()

    # select active borrowings ids for the current item:
    cursor = connections['default'].cursor()
    item_instance_ids = [i.id for i in item_instances]
    active_borrowings_id = {}
    if item_instance_ids:
        active_borrowing_ids = cursor.execute("""
        SELECT `core_borrowing`.`item_id` AS iteminstance_id, `core_borrowing`.`id` AS borrowing_id
        FROM `core_borrowing`
        WHERE `core_borrowing`.`item_id` IN %s AND `core_borrowing`.`returned` IS NULL
        ORDER BY iteminstance_id ASC""", [item_instance_ids])
        active_borrowings_id = dict(cursor.fetchall())

    return render(request, 'item_detail.html',
                  context={'item': item,
                           'authors': authors,
                           'genres': genres,
                           'item_instances': item_instances,
                           'active_borrowings_id': active_borrowings_id,
                           'n_instances': n_instances, }
                  )


def itemListView(request):
    """ View function for homepage of site """
    context = {}
    # update fees and bans
    update_fees_and_bans(datetime.datetime.now())  # + datetime.timedelta(days=0)

    num_items = Item.objects.all().count()
    print(f"num items = {num_items}")
    num_instances = ItemInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = ItemInstance.objects.filter(status='a').count()

    items = Item.objects.prefetch_related('author', 'genre').all()

    items_raw = Item.objects.raw("SELECT * FROM core_item")

    context['items'] = zip(items_raw, items)

    context['num_books'] = len([i for i in items_raw if i.type == "book"])
    context['num_cds'] = len([i for i in items_raw if i.type == "cd"])
    context['num_dvds'] = len([i for i in items_raw if i.type == "dvd"])

    context['page_title'] = "Library Items"

    return render(request, 'index.html', context=context)


class ItemInstanceCreateView(CreateView):
    template_name = 'iteminstance-create.html'
    form_class = ItemInstanceForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('item-detail', kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_by_pk(Item, self.kwargs['pk'])
        context['item'] = item
        return context

    def form_valid(self, form):
        form.instance.item = get_object_by_pk(Item, self.kwargs['pk'])
        # save object to db using raw SQL helpher function
        save_object_to_db(form.instance)
        return HttpResponseRedirect(self.get_success_url())


def ItemInstanceDeleteView(request, pk):
    """
    Confirm delete view
    """
    obj = get_object_by_pk(ItemInstance, pk)
    success_url = reverse_lazy('item-detail', kwargs={'pk': obj.item_id})

    if request.method == "POST":
        obj.delete()
        return HttpResponseRedirect(success_url)

    context = {
        "object": obj,
        "success_url": success_url,
    }
    return render(request, "iteminstance_confirm_delete.html", context)


def ItemInstanceDetailView(request, pk):
    """ redirect to item detail"""
    cursor = connections['default'].cursor()
    cursor.execute(f"""SELECT item_id FROM core_iteminstance WHERE id = {pk}""")
    return redirect('item-detail', pk=cursor.fetchall()[0][0])


def ItemInstanceUpdateView(request, pk):
    """
    View to update the condition of the book
    """
    context = {}
    # fetch the object related to passed pk
    obj = get_object_by_pk(ItemInstance, pk=pk)
    success_url = reverse_lazy('item-detail', kwargs={'pk': obj.item_id})
    # pass the object as instance in form
    form = ItemInstanceForm(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(success_url)

    # add form dictionary to context
    context["form"] = form
    context["success_url"] = success_url
    context["object"] = obj

    return render(request, "iteminstance_update_form.html", context)


def ItemInstanceMakeToggleAvailability(request, pk):
    """
    if iteminstance is unavailable, make available and vice-versa
    """
    iteminstance = get_object_by_pk(ItemInstance, pk)
    if iteminstance.status == "a":
        update_iteminstance_status(iteminstance, "u")
    elif iteminstance.status == "u":
        update_iteminstance_status(iteminstance, "a")

    return HttpResponseRedirect(reverse_lazy('item-detail', kwargs={'pk': iteminstance.item_id}))


# Borrowings ---------------------------------------------

class BorrowingCreateView(CreateView):
    template_name = 'borrowing-create.html'
    form_class = BorrowingForm

    def get_initial(self):
        initial = super().get_initial()
        initial['item'] = get_object_by_pk(ItemInstance, self.kwargs['pk'])
        return initial

    def get_success_url(self, item_id):
        return reverse_lazy('item-detail', kwargs={'pk': item_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_instance = get_object_by_pk(ItemInstance, self.kwargs['pk'])
        context['item_instance'] = item_instance
        return context

    def form_valid(self, form):
        print(form.instance.item)
        print(form.instance.item)
        print(form.instance.item)
        print(form.instance.item)
        print(form.instance.item)
        print(form.instance.item)
        form.instance.item = get_object_by_pk(ItemInstance, self.kwargs['pk'])
        # save object to db using raw SQL helpher function
        if form.instance.item.status == "a":
            form.instance.borrowed = datetime.date.today()
            save_object_to_db(form.instance)
            # update status of itemInstance
            update_iteminstance_status(form.instance.item, "l")
        else:
            print("Book unavailable")

        return HttpResponseRedirect(self.get_success_url(form.instance.item.item_id))


def BorrowingDetailView(request, pk):
    context = {}
    # Select the item (using raw SQL with helper function)
    borrowing = get_object_by_pk(Borrowing, pk)
    # get related iteminstance
    borrowing.borrower = get_object_by_pk(User, borrowing.borrower_id)
    # get related item title
    item = get_object_by_pk(Item, borrowing.item.item_id)
    # get related user :
    if borrowing.item_id:
        borrowing.item = get_object_by_pk(ItemInstance, borrowing.item_id)

    context['borrowing'] = borrowing
    context['item'] = item
    return render(request, 'borrowing_detail.html', context=context)


def BorrowingExtendOneWeek(request, pk):
    """
    extend due_date by 1 week
    """
    borrowing = get_object_by_pk(Borrowing, pk)
    new_due_date = borrowing.due_date + datetime.timedelta(weeks=1)
    update_borrowing_due_date(borrowing, new_due_date)

    return HttpResponseRedirect(reverse_lazy('borrowing-detail', kwargs={'pk': borrowing.id}))


def BorrowingMarkAsReturned(request, pk):
    """
        Mark as returned with current date and set related iteminstance to available
    """
    borrowing = get_object_by_pk(Borrowing, pk)
    return_datetime = datetime.datetime.now()
    update_borrowing_returned(borrowing, return_datetime)

    itemintance = get_object_by_pk(ItemInstance, borrowing.item_id)
    update_iteminstance_status(itemintance, "a")

    return HttpResponseRedirect(reverse_lazy('borrowing-detail', kwargs={'pk': pk}))


# User Views ---------------------------------

def UserListView(request):
    context = {}
    users = User.objects.raw("SELECT * FROM `core_user`")

    context['users'] = users
    context['n_users'] = users.__len__()

    # get situations
    cursor = connections['default'].cursor()
    user_situation_ids = list(set([i.situation_id for i in users]))

    situation_names = cursor.execute("""
           SELECT core_situation.id, core_situation.situation
           FROM core_situation
           WHERE core_situation.id IN %s""", [user_situation_ids])
    situation_dict = dict(cursor.fetchall())
    context['situations'] = situation_dict

    # get number of borrowed items
    cursor = connections['default'].cursor()
    user_ids = [u.id for u in users]
    cursor.execute("""
    SELECT borrower_id, COUNT(*)
    FROM core_borrowing
    WHERE returned IS NULL
    GROUP BY borrower_id;
    """)
    n_borrowed_items = dict(cursor.fetchall())
    context['n_borrowed_items'] = n_borrowed_items

    return render(request, 'user_list.html', context=context)


def UserDetailView(request, pk):
    context = {}
    user = get_object_by_pk(User, pk)
    context['user'] = user

    # get related situation
    if user.situation_id:
        user.situation = get_object_by_pk(Situation, user.situation_id)

    # get all borrowings
    borrowings = Borrowing.objects.raw(f"""
    SELECT * FROM core_borrowing
    WHERE `core_borrowing`.`borrower_id` IN ({user.id})
    ORDER BY `core_borrowing`.`borrowed` ASC
    """)
    active_borrowings = [b for b in borrowings if not b.returned]
    returned = [b for b in borrowings if b.returned]
    context['active_borrowings'] = active_borrowings
    context['returned'] = returned

    # get title names for borrowings:
    cursor = connections['default'].cursor()
    iteminstance_ids = [b.item_id for b in borrowings]
    if iteminstance_ids != []:
        cursor.execute("""SELECT core_iteminstance.id ,title
        FROM core_iteminstance
        LEFT JOIN core_item 
        ON (core_iteminstance.item_id = core_item.id)
        WHERE core_iteminstance.id IN %s
        """, [iteminstance_ids])
        titles = dict(cursor.fetchall())
        context["titles"] = titles


    context['t_overdue_fees'] = sum([b.overdue_fee for b in borrowings if b.overdue_fee_payed == False])

    return render(request, 'user_detail.html', context=context)


# Item

class ItemCreateView(CreateView):
    template_name = 'item_create.html'
    form_class = ItemForm
    success_url = reverse_lazy("index")


class ItemUpdateView(UpdateView):
    model = Item
    template_name = 'item_update.html'
    form_class = ItemForm
    success_url = reverse_lazy("index")


def PayOverdueFee(request, pk):
    borrowing = get_object_by_pk(Borrowing, pk)
    if borrowing.returned:
        borrowing.overdue_fee_payed = True
        borrowing.save()
    return HttpResponseRedirect(reverse_lazy('borrowing-detail', kwargs={'pk': pk}))