from django.db import connections
from django.forms import model_to_dict


def get_object_by_pk(model, pk):
    """
    select and filter by pk
    """
    table_name = model._meta.db_table
    pk_name = model._meta.pk.name
    return model.objects.raw(f"""
            SELECT *
            FROM `{table_name}`
            WHERE `{table_name}`.`{pk_name}` = {pk}
            LIMIT 1
            """)[0]


def save_object_to_db(obj_instance, auto_increment=True):
    """
    save object instance to db with raw sql query
    """
    table_name = obj_instance._meta.db_table
    pk_name = obj_instance._meta.pk.name

    obj_dict = model_to_dict(obj_instance)
    # remove pk field to allow auto increment
    if auto_increment:
        obj_dict.pop(pk_name, None)
    column_names = ",".join([f"`{obj_instance._meta.get_field(s).column}`" for s in obj_dict.keys()])
    values = tuple(obj_dict.values())

    cursor = connections['default'].cursor()

    # use query params %s to prevent SQL injection on user input
    cursor.execute(f"""INSERT INTO `{table_name}` ({column_names}) VALUES %s""",
                   [values])
    print(cursor)


def delete_object(obj_instance):
    cursor = connections['default'].cursor()
    table_name = obj_instance._meta.db_table
    pk_name = obj_instance._meta.pk.name

    cursor.execute(f"""DELETE FROM `{table_name}`
    WHERE `{table_name}`.`{pk_name}` IN ({obj_instance.pk})""")


def update_object(obj_instance):
    cursor = connections['default'].cursor()
    table_name = obj_instance._meta.db_table
    pk_name = obj_instance._meta.pk.name

    pass


def update_iteminstance_status(iteminstance, status):
    cursor = connections['default'].cursor()
    table_name = iteminstance._meta.db_table
    pk_name = iteminstance._meta.pk.name
    pk = iteminstance.pk

    cursor.execute(f"""
    UPDATE `{table_name}`
    SET `status` = '{status}'
    WHERE `{table_name}`.`id` = {pk}
    """)


def update_borrowing_due_date(borrowing, new_date):
    cursor = connections['default'].cursor()
    table_name = borrowing._meta.db_table
    pk_name = borrowing._meta.pk.name
    pk = borrowing.pk
    cursor.execute(f"""
       UPDATE `{table_name}`
       SET `due_date` = %s
       WHERE `{table_name}`.`id` = {pk}
       """, [new_date])


def update_borrowing_returned(borrowing, new_date):
    cursor = connections['default'].cursor()
    table_name = borrowing._meta.db_table
    pk_name = borrowing._meta.pk.name
    pk = borrowing.pk
    cursor.execute(f"""
       UPDATE `{table_name}`
       SET `returned` = %s
       WHERE `{table_name}`.`id` = {pk}
       """, [new_date])


def update_borrowing_overdue_fee(borrowing, overdue_fee):
    cursor = connections['default'].cursor()
    table_name = borrowing._meta.db_table
    pk_name = borrowing._meta.pk.name
    pk = borrowing.pk
    cursor.execute(f"""
           UPDATE `{table_name}`
           SET `overdue_fee` = %s
           WHERE `{table_name}`.`id` = {pk}
           """, [overdue_fee])
