# Generated for Market Bridge marketplace listings and orders.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0003_notification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('buyer', 'Buyer'), ('seller', 'Seller'), ('both', 'Buyer and seller')], default='both', max_length=12)),
                ('is_approved', models.BooleanField(default=True)),
                ('business_name', models.CharField(blank=True, max_length=140)),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('address', models.CharField(blank=True, max_length=220)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='market_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__username'],
            },
        ),
        migrations.CreateModel(
            name='MarketListing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_type', models.CharField(choices=[('inventory', 'From stock'), ('manual', 'Manual stock')], default='manual', max_length=16)),
                ('species', models.CharField(max_length=120)),
                ('title', models.CharField(max_length=160)),
                ('quantity_kg', models.DecimalField(decimal_places=2, max_digits=10)),
                ('available_quantity_kg', models.DecimalField(decimal_places=2, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('suggested_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('location', models.CharField(max_length=180)),
                ('available_from', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('photo', models.FileField(blank=True, null=True, upload_to='market_bridge/listings/')),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('sold_out', 'Sold out'), ('closed', 'Closed')], default='active', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fish_stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='market_listings', to='store.fishstock')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='market_listings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MarketOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_kg', models.DecimalField(decimal_places=2, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=16)),
                ('buyer_note', models.TextField(blank=True)),
                ('seller_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='market_orders', to=settings.AUTH_USER_MODEL)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='market_bridge.marketlisting')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='marketlisting',
            index=models.Index(fields=['status', '-created_at'], name='mb_listing_status_idx'),
        ),
        migrations.AddIndex(
            model_name='marketlisting',
            index=models.Index(fields=['seller', 'status'], name='mb_listing_seller_status_idx'),
        ),
        migrations.AddIndex(
            model_name='marketlisting',
            index=models.Index(fields=['species', 'location'], name='mb_listing_species_loc_idx'),
        ),
        migrations.AddIndex(
            model_name='marketorder',
            index=models.Index(fields=['buyer', 'status', '-created_at'], name='mb_order_buyer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='marketorder',
            index=models.Index(fields=['listing', 'status'], name='mb_order_listing_status_idx'),
        ),
        migrations.AddConstraint(
            model_name='marketlisting',
            constraint=models.CheckConstraint(condition=models.Q(('quantity_kg__gt', 0)), name='market_listing_quantity_positive'),
        ),
        migrations.AddConstraint(
            model_name='marketlisting',
            constraint=models.CheckConstraint(condition=models.Q(('available_quantity_kg__gte', 0)), name='market_listing_available_not_negative'),
        ),
        migrations.AddConstraint(
            model_name='marketlisting',
            constraint=models.CheckConstraint(condition=models.Q(('unit_price__gt', 0)), name='market_listing_unit_price_positive'),
        ),
        migrations.AddConstraint(
            model_name='marketlisting',
            constraint=models.CheckConstraint(condition=models.Q(('suggested_price__isnull', True), ('suggested_price__gt', 0), _connector='OR'), name='market_listing_suggested_price_positive'),
        ),
        migrations.AddConstraint(
            model_name='marketorder',
            constraint=models.CheckConstraint(condition=models.Q(('quantity_kg__gt', 0)), name='market_order_quantity_positive'),
        ),
        migrations.AddConstraint(
            model_name='marketorder',
            constraint=models.CheckConstraint(condition=models.Q(('unit_price__gt', 0)), name='market_order_unit_price_positive'),
        ),
        migrations.AddConstraint(
            model_name='marketorder',
            constraint=models.CheckConstraint(condition=models.Q(('total_price__gt', 0)), name='market_order_total_price_positive'),
        ),
    ]
