from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ComplaintForm, RegistrationForm, StaffComplaintForm
from .models import Complaint, Crew


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your citizen account is ready.')
        return redirect('dashboard')
    return render(request, 'complaints/register.html', {'form': form})


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    complaints = Complaint.objects.filter(submitted_by=request.user)
    return render(request, 'complaints/dashboard.html', {
        'complaints': complaints,
        'total_count': complaints.count(),
        'active_count': complaints.exclude(
            status__in=(Complaint.Status.RESOLVED, Complaint.Status.CLOSED)
        ).count(),
        'closed_count': complaints.filter(status=Complaint.Status.CLOSED).count(),
    })


@login_required
def complaint_create(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    form = ComplaintForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        complaint = form.save(commit=False)
        complaint.submitted_by = request.user
        complaint.save()
        messages.success(request, 'Your complaint has been submitted for review.')
        return redirect('complaint_detail', reference=complaint.reference)
    return render(request, 'complaints/complaint_form.html', {'form': form})


@login_required
def complaint_detail(request, reference):
    complaint = get_object_or_404(Complaint, reference=reference)
    is_owner = complaint.submitted_by_id == request.user.id
    is_crew_leader = (
        complaint.assigned_crew_id is not None
        and complaint.assigned_crew.leader_id == request.user.id
    )
    if not (request.user.is_staff or is_owner or is_crew_leader):
        return redirect('dashboard')
    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint,
        'can_start_work': is_crew_leader and complaint.status == Complaint.Status.ASSIGNED,
        'can_upload_proof': is_crew_leader and complaint.status == Complaint.Status.IN_PROGRESS,
    })


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    complaints = Complaint.objects.select_related(
        'submitted_by', 'assigned_crew',
    )
    return render(request, 'complaints/admin_dashboard.html', {
        'complaints': complaints,
        'total_count': complaints.count(),
        'unassigned_count': complaints.filter(
            assigned_crew__isnull=True,
        ).exclude(status=Complaint.Status.CLOSED).count(),
        'active_count': complaints.filter(
            status__in=(Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS),
        ).count(),
        'resolved_count': complaints.filter(status=Complaint.Status.RESOLVED).count(),
        'crews': Crew.objects.all(),
    })


@login_required
@user_passes_test(is_staff)
def complaint_update(request, reference):
    complaint = get_object_or_404(
        Complaint.objects.select_related('assigned_crew'),
        reference=reference,
    )
    form = StaffComplaintForm(request.POST or None, instance=complaint)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
            previous_crew = complaint.assigned_crew
            updated = form.save(commit=False)
            if updated.assigned_crew_id and updated.status == Complaint.Status.SUBMITTED:
                updated.status = Complaint.Status.ASSIGNED
            updated.save()
            if previous_crew and previous_crew != updated.assigned_crew:
                previous_crew.is_available = True
                previous_crew.save(update_fields=('is_available',))
            if updated.assigned_crew and updated.status not in (
                Complaint.Status.RESOLVED,
                Complaint.Status.CLOSED,
            ):
                updated.assigned_crew.is_available = False
                updated.assigned_crew.save(update_fields=('is_available',))
            elif updated.assigned_crew:
                updated.assigned_crew.is_available = True
                updated.assigned_crew.save(update_fields=('is_available',))
        messages.success(request, 'Complaint review has been saved.')
        return redirect('complaint_detail', reference=complaint.reference)
    return render(request, 'complaints/complaint_update.html', {
        'form': form,
        'complaint': complaint,
    })


@login_required
def upload_completion_proof(request, reference):
    complaint = get_object_or_404(
        Complaint.objects.select_related('assigned_crew'),
        reference=reference,
    )
    if (
        complaint.assigned_crew is None
        or complaint.assigned_crew.leader_id != request.user.id
    ):
        return redirect('dashboard')
    if complaint.status != Complaint.Status.IN_PROGRESS:
        messages.error(request, 'Completion proof can only be submitted for work in progress.')
        return redirect('complaint_detail', reference=complaint.reference)
    if request.method == 'POST' and request.FILES.get('completion_proof'):
        complaint.completion_proof = request.FILES['completion_proof']
        complaint.status = Complaint.Status.RESOLVED
        complaint.save(update_fields=(
            'completion_proof', 'status', 'updated_at',
        ))
        crew = complaint.assigned_crew
        crew.is_available = True
        crew.save(update_fields=('is_available',))
        messages.success(request, 'Completion proof uploaded for administrator verification.')
    else:
        messages.error(request, 'Choose a proof file before submitting.')
    return redirect('complaint_detail', reference=complaint.reference)


@login_required
def start_work(request, reference):
    complaint = get_object_or_404(
        Complaint.objects.select_related('assigned_crew'),
        reference=reference,
    )
    if (
        complaint.assigned_crew is None
        or complaint.assigned_crew.leader_id != request.user.id
    ):
        return redirect('dashboard')
    if request.method == 'POST' and complaint.status == Complaint.Status.ASSIGNED:
        complaint.status = Complaint.Status.IN_PROGRESS
        complaint.save(update_fields=('status', 'updated_at'))
        messages.success(request, 'Work started. Upload completion proof after resolving the issue.')
    return redirect('complaint_detail', reference=complaint.reference)
