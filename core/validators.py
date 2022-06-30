from django.core.exceptions import ValidationError
from django.db import connections


def validate_loan(user, iteminstance):
    """
    A user can borrow only 3 books and 2 cds/dvds, a user must not be banned
    """
    max_books = 3
    max_other = 2
    cursor = connections['default'].cursor()

    # get type counts for current borrowed items
    cursor.execute("""
        SELECT `type`, COUNT(*) FROM core_borrowing
    LEFT JOIN core_iteminstance AS inst ON (inst.id = core_borrowing.item_id)
	LEFT JOIN core_item AS it ON (it.id = inst.item_id)
	WHERE `core_borrowing`.`borrower_id` = %s AND returned IS NULL 
	GROUP BY `type`
    """, [user.id])
    count_dict = dict(cursor.fetchall())
    book_count = count_dict.get("book", 0)
    other_count = count_dict.get("cd", 0) + count_dict.get("dvd", 0)

    if book_count >= max_books and iteminstance.item.type == "book" :
        raise ValidationError(
            f'This user has already borrowed the maximum number of books',
        )
    if (other_count >= max_other and ( iteminstance.item.type == "cd" or iteminstance.item.type == "dvd")):
        raise ValidationError(
            f'This user has already borrowed the maximum number of CDs/DVDs',
        )

    if (user.banned_until):
        raise ValidationError(
            f'This user is banned until {user.banned_until}',
        )

