import uuid

from django.conf import settings
from django.db import models


class Crew(models.Model):
	name = models.CharField(max_length=120, unique=True)
	leader = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='led_crews',
	)
	contact_number = models.CharField(max_length=30, blank=True)
	is_available = models.BooleanField(default=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Complaint(models.Model):
	class Category(models.TextChoices):
		HOUSEHOLD = 'household', 'Household waste'
		RECYCLING = 'recycling', 'Recycling'
		BULKY = 'bulky', 'Bulky waste'
		HAZARDOUS = 'hazardous', 'Hazardous waste'
		MISSED_COLLECTION = 'missed_collection', 'Missed collection'
		OTHER = 'other', 'Other'

	class Priority(models.TextChoices):
		LOW = 'low', 'Low'
		NORMAL = 'normal', 'Normal'
		HIGH = 'high', 'High'
		URGENT = 'urgent', 'Urgent'

	class Status(models.TextChoices):
		SUBMITTED = 'submitted', 'Submitted'
		UNDER_REVIEW = 'under_review', 'Under review'
		ASSIGNED = 'assigned', 'Assigned'
		IN_PROGRESS = 'in_progress', 'In progress'
		RESOLVED = 'resolved', 'Resolved'
		CLOSED = 'closed', 'Closed'

	reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	submitted_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='complaints',
	)
	category = models.CharField(max_length=24, choices=Category.choices)
	description = models.TextField()
	location = models.CharField(max_length=240)
	priority = models.CharField(
		max_length=12,
		choices=Priority.choices,
		default=Priority.NORMAL,
	)
	status = models.CharField(
		max_length=16,
		choices=Status.choices,
		default=Status.SUBMITTED,
	)
	assigned_crew = models.ForeignKey(
		Crew,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='complaints',
	)
	completion_proof = models.FileField(
		upload_to='complaint_proofs/%Y/%m/',
		blank=True,
	)
	submitted_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-submitted_at']

	def __str__(self):
		return f'Complaint {str(self.reference)[:8]}'
