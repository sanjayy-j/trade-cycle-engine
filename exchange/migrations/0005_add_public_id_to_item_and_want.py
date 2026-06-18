import uuid

from django.db import migrations, models


def generate_public_ids(apps, schema_editor):
    Item = apps.get_model('exchange', 'Item')
    Want = apps.get_model('exchange', 'Want')

    for item in Item.objects.all():
        item.public_id = uuid.uuid4()
        item.save(update_fields=['public_id'])

    for want in Want.objects.all():
        want.public_id = uuid.uuid4()
        want.save(update_fields=['public_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0004_item_updated_at_alter_item_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='public_id',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='want',
            name='public_id',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(generate_public_ids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='item',
            name='public_id',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name='want',
            name='public_id',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
