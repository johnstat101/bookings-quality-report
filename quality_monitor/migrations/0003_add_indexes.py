# Generated manually for optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality_monitor', '0002_auto_20250919_1800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pnr',
            name='control_number',
            field=models.CharField(db_index=True, max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='pnr',
            name='office_id',
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='pnr',
            name='creation_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='pnr',
            name='delivery_system_company',
            field=models.CharField(blank=True, db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='contact',
            name='contact_type',
            field=models.CharField(choices=[('AP', 'AP'), ('APE', 'APE'), ('APM', 'APM'), ('CTCE', 'CTCE'), ('CTCEM', 'CTCEM'), ('CTCM', 'CTCM')], db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='contact',
            name='contact_detail',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AddIndex(
            model_name='pnr',
            index=models.Index(fields=['creation_date', 'office_id'], name='quality_mon_creatio_idx'),
        ),
        migrations.AddIndex(
            model_name='pnr',
            index=models.Index(fields=['delivery_system_company', 'creation_date'], name='quality_mon_deliver_idx'),
        ),
        migrations.AddIndex(
            model_name='contact',
            index=models.Index(fields=['contact_type', 'contact_detail'], name='quality_mon_contact_idx'),
        ),
    ]