from django.contrib import admin

from .models import Complaint, Crew


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
	list_display = ('name', 'leader', 'contact_number', 'is_available')
	list_filter = ('is_available',)
	search_fields = ('name', 'leader__username')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
	list_display = (
		'reference',
		'category',
		'priority',
		'status',
		'assigned_crew',
		'submitted_at',
	)
	list_filter = ('status', 'priority', 'category')
	search_fields = ('reference', 'location', 'submitted_by__username')
	readonly_fields = ('reference', 'submitted_at', 'updated_at')
