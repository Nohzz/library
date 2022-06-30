import datetime

from django.db import connections

from core.models import Borrowing, User
from sqlhelpers import update_borrowing_overdue_fee


def update_fees_and_bans(now):
    """
    """
    not_returned_borrowings = Borrowing.objects.raw("""
    SELECT * FROM core_borrowing WHERE returned is NULL
    """)

    for borrowing in not_returned_borrowings:
        # if overdue
        if now > borrowing.due_date:
            # update overdue fee
            overdue_days = (now - borrowing.due_date).days
            overdue_fee = overdue_days - 3
            update_borrowing_overdue_fee(borrowing, overdue_fee)

    users = User.objects.raw("""SELECT * FROM core_user""")

    for user in users:
        twelve_months_ago = now - datetime.timedelta(days=365)
        cursor = connections['default'].cursor()
        cursor.execute("""SELECT COUNT(*) FROM core_borrowing
        WHERE borrower_id = %s AND overdue_fee > 0 AND due_date > %s;""", [ user.id,twelve_months_ago])
        overdue_borrowings_in_last_twelve_months = cursor.fetchone()[0]
        print(f""" User = {user} 
                    12 : {twelve_months_ago}
                    overdue_borrowings_in_last_twelve_months = {overdue_borrowings_in_last_twelve_months} 
                    banned_until =  {user.banned_until}""")
        print("aaaaaaaaaaaaaaaaa", type(now), type(user.banned_until), user.banned_until)
        if overdue_borrowings_in_last_twelve_months >= 3:
            # ban user for two years
            # last overdue date :
            cursor = connections['default'].cursor()
            cursor.execute("""SELECT max(due_date)
                                FROM core_borrowing
                                WHERE borrower_id = %s
                                AND overdue_fee > 0;""", [user.id])
            ban_start_date = cursor.fetchone()[0]
            user.banned_until = ban_start_date + datetime.timedelta(days=730)
            user.save()
        elif user.banned_until and now > user.banned_until:
            user.banned_until = None
            user.save()
