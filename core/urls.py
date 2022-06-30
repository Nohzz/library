from django.urls import path
from . import views

urlpatterns = [
    path('', views.itemListView, name='index'),
    path('items/', views.itemListView, name='itemListView'),
    path('item/<int:pk>', views.ItemDetailView, name='item-detail'),

    # ItemInstance
    path('iteminstance/create/<int:pk>', views.ItemInstanceCreateView.as_view(), name='iteminstance-create'),
    path('iteminstance/delete/<int:pk>', views.ItemInstanceDeleteView, name='iteminstance-delete'),
    path('iteminstance/update/<int:pk>', views.ItemInstanceUpdateView, name='iteminstance-update'),
    path('iteminstance/toggleavailability/<int:pk>', views.ItemInstanceMakeToggleAvailability,
         name="iteminstance-toggle"),
    path('iteminstance/detail/<int:pk>', views.ItemInstanceDetailView, name='iteminstance-detail'),

    # Borrowing
    path('borrowing/create/<int:pk>', views.BorrowingCreateView.as_view(), name='borrowing-create'),
    path('borrowing/<int:pk>', views.BorrowingDetailView, name='borrowing-detail'),
    path('borrowing/extend/<int:pk>', views.BorrowingExtendOneWeek, name='borrowing-extend'),
    path('borrowing/returned/<int:pk>', views.BorrowingMarkAsReturned, name='borrowing-returned'),
    path('borrowing/pay/<int:pk>', views.PayOverdueFee, name="borrowing-pay"),

    # User
    path('users/', views.UserListView, name='user-list'),
    path('user/<int:pk>', views.UserDetailView, name='user-detail'),

    # Date update:
    # path('updatetime/', views.UpdateTime, name='update')

    # Item
    path('item/create', views.ItemCreateView.as_view(), name="item-create"),
    path('item/update/<int:pk>', views.ItemUpdateView.as_view(), name="item-update")


]
