from django.db import migrations, models, connection


def ensure_author_column(apps, schema_editor):
    Book = apps.get_model('books', 'Book')
    table_name = Book._meta.db_table

    with connection.cursor() as cursor:
        existing_columns = {
            column.name for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'author' not in existing_columns:
        field = models.CharField(max_length=255, blank=True, default='')
        field.set_attributes_from_name('author')
        schema_editor.add_field(Book, field)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_book_location'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_author_column, noop),
            ],
            state_operations=[],
        ),
    ]
