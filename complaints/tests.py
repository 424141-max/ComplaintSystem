from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Complaint, Crew


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ComplaintWorkflowTests(TestCase):
	def setUp(self):
		self.citizen = User.objects.create_user(
			username='citizen',
			email='citizen@example.com',
			password='Strong-password-123',
		)
		self.staff = User.objects.create_user(
			username='operator',
			password='Strong-password-123',
			is_staff=True,
		)
		self.crew_leader = User.objects.create_user(
			username='crew-leader',
			password='Strong-password-123',
		)
		self.crew = Crew.objects.create(name='North Route', leader=self.crew_leader)
		self.complaint = Complaint.objects.create(
			submitted_by=self.citizen,
			category=Complaint.Category.HOUSEHOLD,
			description='Collection was missed this morning.',
			location='14 Maple Street',
		)
		self.media_dir = TemporaryDirectory()
		self.addCleanup(self.media_dir.cleanup)
		media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
		media_settings.enable()
		self.addCleanup(media_settings.disable)

	def test_citizen_pages_render(self):
		self.client.force_login(self.citizen)

		self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
		self.assertEqual(self.client.get(reverse('complaint_create')).status_code, 200)
		self.assertEqual(self.client.get(reverse(
			'complaint_detail', args=(self.complaint.reference,),
		)).status_code, 200)

	def test_staff_dashboard_renders(self):
		self.client.force_login(self.staff)

		response = self.client.get(reverse('admin_dashboard'))

		self.assertContains(response, 'Complaint control room')

	def test_registration_creates_citizen_account(self):
		page = self.client.get(reverse('register'))
		for field_name in ('password1', 'password2'):
			widget = page.context['form'].fields[field_name].widget
			self.assertEqual(widget.input_type, 'text')
			self.assertNotIn('data-password-toggle', widget.attrs)

		response = self.client.post(reverse('register'), {
			'username': 'new-citizen',
			'email': 'new@example.com',
			'password1': 'Unique-password-907!',
			'password2': 'Unique-password-907!',
		})

		self.assertRedirects(response, reverse('dashboard'))
		self.assertTrue(User.objects.filter(username='new-citizen').exists())

	def test_citizen_can_only_view_their_own_complaint(self):
		other_citizen = User.objects.create_user(
			username='other', password='Strong-password-123',
		)
		self.client.force_login(other_citizen)

		response = self.client.get(reverse(
			'complaint_detail', args=(self.complaint.reference,),
		))

		self.assertRedirects(response, reverse('dashboard'))

	def test_staff_assignment_marks_crew_unavailable(self):
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse('complaint_update', args=(self.complaint.reference,)),
			{
				'priority': Complaint.Priority.HIGH,
				'status': Complaint.Status.ASSIGNED,
				'assigned_crew': self.crew.pk,
			},
		)

		self.assertRedirects(response, reverse(
			'complaint_detail', args=(self.complaint.reference,),
		))
		self.crew.refresh_from_db()
		self.complaint.refresh_from_db()
		self.assertFalse(self.crew.is_available)
		self.assertEqual(self.complaint.assigned_crew, self.crew)

	def test_crew_leader_uploads_proof_and_resolves_complaint(self):
		self.complaint.assigned_crew = self.crew
		self.complaint.status = Complaint.Status.IN_PROGRESS
		self.complaint.save()
		self.crew.is_available = False
		self.crew.save()
		self.client.force_login(self.crew_leader)

		response = self.client.post(
			reverse('upload_completion_proof', args=(self.complaint.reference,)),
			{'completion_proof': SimpleUploadedFile('proof.txt', b'Work completed.')},
		)

		self.assertRedirects(response, reverse(
			'complaint_detail', args=(self.complaint.reference,),
		))
		self.complaint.refresh_from_db()
		self.crew.refresh_from_db()
		self.assertEqual(self.complaint.status, Complaint.Status.RESOLVED)
		self.assertTrue(self.complaint.completion_proof.name)
		self.assertTrue(self.crew.is_available)

	def test_crew_leader_can_start_assigned_work(self):
		self.complaint.assigned_crew = self.crew
		self.complaint.status = Complaint.Status.ASSIGNED
		self.complaint.save()
		self.client.force_login(self.crew_leader)

		response = self.client.post(reverse(
			'start_work', args=(self.complaint.reference,),
		))

		self.assertRedirects(response, reverse(
			'complaint_detail', args=(self.complaint.reference,),
		))
		self.complaint.refresh_from_db()
		self.assertEqual(self.complaint.status, Complaint.Status.IN_PROGRESS)

	def test_crew_leader_cannot_upload_proof_to_closed_complaint(self):
		self.complaint.assigned_crew = self.crew
		self.complaint.status = Complaint.Status.CLOSED
		self.complaint.save()
		self.client.force_login(self.crew_leader)

		response = self.client.post(
			reverse('upload_completion_proof', args=(self.complaint.reference,)),
			{'completion_proof': SimpleUploadedFile('proof.txt', b'Work completed.')},
		)

		self.assertRedirects(response, reverse(
			'complaint_detail', args=(self.complaint.reference,),
		))
		self.complaint.refresh_from_db()
		self.assertEqual(self.complaint.status, Complaint.Status.CLOSED)
		self.assertFalse(self.complaint.completion_proof)

	def test_staff_cannot_close_without_completion_proof(self):
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse('complaint_update', args=(self.complaint.reference,)),
			{
				'priority': Complaint.Priority.NORMAL,
				'status': Complaint.Status.CLOSED,
				'assigned_crew': '',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'completion proof')
		self.complaint.refresh_from_db()
		self.assertEqual(self.complaint.status, Complaint.Status.SUBMITTED)
