from distutils import errors
import imp
from unicodedata import category
from urllib.request import Request
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.template import RequestContext
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import transaction
from django.views.generic import View, TemplateView, ListView, DetailView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.conf import settings
from . models import *
from . forms import *
from . forms import RegisterForm
import json
import re
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from . decorators import unauthenticated_user, allowed_users, admin_only, unauthenticated_user
from json import dumps as jdumps
import sweetify
from . utils import generate_token
import threading
from itertools import chain

# Create your views here.

#---------------------------------------------------------------------------------------------------
#------GENERAL ----------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
class FullnameValidatorView(View):
    def post(self, request):
        data = json.loads(request.body)
        full_name = data['full_name']

        if not re.match(r'^[a-zA-Z]+\s[a-zA-Z]*$', str(full_name)):
            return JsonResponse({'full_name_error':'Please input only two names without digits or special characters'}, status=400)
        elif len(str(full_name)) < 6:
            return JsonResponse({'full_name_error':'Full name is too short'}, status=409)

        return JsonResponse({'fullname_valid': True})

class EmailValidatorView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']

        if User.objects.filter(email=str(email)).exists():
            return JsonResponse({'email_error':'User with this email already exists'}, status=409)

        return JsonResponse({'email_valid': True})

class PasswordValidatorView(View):
    def post(self, request):
        data = json.loads(request.body)
        password1 = data['password1']

        if len(str(password1)) < 8:
            return JsonResponse({'password_error':'Password is too short'}, status=400)
        
        return JsonResponse({'password_valid': True})

class ReferralcodeValidatorView(View):
    def post(self, request):
        data = json.loads(request.body)
        ref_code = data['ref_code']

        if not Worker.objects.filter(code=ref_code).exists():
            return JsonResponse({'ref_code_error':'Referral code does not exist!'}, status=400)
        return JsonResponse({'refcode_valid': True})
    
@unauthenticated_user
def home(request):

    form = SuscribersForm()
    form1 = ContactForm()

    if request.method == 'POST':
        try:
            if request.POST['name']:
                form1 = ContactForm(request.POST)
                if form1.is_valid():
                    form1.save()
                    sweetify.success(request, title='Message Received',
                                     text='Thank you for contacting us. We\'ll get back to you shortly.',
                                     icon='success',
                                     button='Ok', extra_tags='contact')
                    return redirect('/')

                else:
                    sweetify.error(request, title='Error',
                                   text='An error occured while trying to send your message.\nPlease try again.\n We sincerely apologize for any inconveniences.',
                                   icon='error', button='Ok', extra_tags='contact')
                    return redirect('/')

        except:
            form = SuscribersForm(request.POST)
            if form.is_valid():
                form.save()
                sweetify.success(request, title='Email Received',
                                 text='You have successfully suscribed to our newsletter',
                                 icon='success', button='Ok', extra_tags='newsletter')
                return redirect('/')
            else:
                print(form.errors)
                sweetify.error(request, title='Error',
                               text = '{}'.format(form.errors['email'].as_text()),
                               icon='error', button='Ok', extra_tags='contact')
                return redirect('/')


    context = {'form':form, 'form1':form1}

    return render(request, 'task/home.html', context)

@unauthenticated_user
def faqs(request):

    faqs = Faqs_Terms.objects.exclude(terms_title__isnull=False, terms_text__isnull=False)

    form = SuscribersForm()

    if request.method == 'POST':
        form = SuscribersForm(request.POST)
        if form.is_valid():
            form.save()
            sweetify.success(request, title='Email Received', text='You have successfully suscribed to our newsletter', icon='success', button='Ok', extra_tags='newsletter')
            return redirect('faqs')
        else:
            sweetify.error(request, title='Error',
                           text = '{}'.format(form.errors['email'].as_text()),
                           icon='error', button='Ok', extra_tags='contact')
            return redirect('faqs')


    context = {'faqs':faqs, 'form':form}
    return render(request,'task/faqs.html', context)

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)
    
    def run(self):
        self.email.send()

def send_activation_email(user, request):
    current_site = get_current_site(request)
    email_subject = 'Activate your account'
    email_body = render_to_string('task/activate.html', {
        'user':user, 
        'domain':current_site, 
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject = email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,
    to = [user.email]
    
    )

    EmailThread(email).start()

@unauthenticated_user
def registerPage(request):
    form = RegisterForm(request)
    if request.method == 'POST':
        form = RegisterForm(request, request.POST)
        if form.is_valid():
            user = form.save()
            send_activation_email(user, request)

            sweetify.success(request, title='Account Created', text='We\'ve sent you an email to verify your account', icon='success', button='Ok', timer=4000)
            
            return redirect('login')

    context = {'form':form}
    
    return render(request, 'task/reg.html', context)

@unauthenticated_user
def registerPage2(request, ref_code):
    referrer = Worker.objects.get(code=ref_code).user
    print(referrer)
    form = RegisterForm(request)
    if request.method == 'POST':
        form = RegisterForm(request, request.POST)
        if form.is_valid():
            user = form.save()
            send_activation_email(user, request)

            sweetify.success(request, title='Account Created', text='We\'ve sent you an email to verify your account', icon='success', button='Ok', timer=4000)
            
            return redirect('login')

    context = {'form':form}
    
    return render(request, 'task/reg.html', context)

@unauthenticated_user
def loginPage(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_email_verified:
                if user.is_staff:
                    login(request, user)
                    sweetify.success(request, title='Success', text='You\'re now logged in', icon='success', button='Ok', timer=3000)
                    return redirect('dashboard')
                else:
                    login(request, user)
                    sweetify.success(request, title='Success', text='You\'re now logged in', icon='success', button='Ok', timer=3000)
                    return redirect('user-page')
            else:
                sweetify.warning(request, title='Warning', text='Email is not verified. Please check your email inbox or spam for verification link', icon='warning', button='Ok', timer=4000)
                return redirect('login')
        else:
            sweetify.error(request, title='Error', text='The email OR password you entered is incorrect', icon='error', button='Ok', timer=3000)
    context = {}
    return render(request, 'task/log.html', context)

@login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')

def activate_user(request, uidb64, token):

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.is_email_verified = True
        user.save()
        if user.worker.recommended_by != None:
            Earnings.objects.create(worker=user.worker, pending_earnings="0", verified_earnings="10", disapproved_earnings="0", withdrawn_earnings="0", paid_earnings="0")
        else:
            Earnings.objects.create(worker=user.worker, pending_earnings="0", verified_earnings="2", disapproved_earnings="0", withdrawn_earnings="0", paid_earnings="0")

        sweetify.success(request, title='Success', text='Email verified, You can now log in', icon='success', button='Ok', timer=3000)
        if user.worker.recommended_by != None:
            referrer = user.worker.recommended_by
            if referrer.is_staff:
                notification3 = Notification.objects.create(notification_type = 11, admin=referrer.worker)
            else:
                notification3 = Notification.objects.create(notification_type = 11, to_worker=referrer.worker)
            earnings = Earnings.objects.get(worker=referrer.worker)
            verified_earnings = earnings.verified_earnings
            earnings.verified_earnings = str(verified_earnings + 10)
            earnings.save() 
        return redirect(reverse('login'))

    return render(request, 'task/activate_failed.html', {"user": user})

@login_required(login_url='login')
def profile(request):

    worker = request.user.worker

    earnings = Earnings.objects.get(worker=worker)
    earnings_total = earnings.get_total_earnings
    pending_earnings = earnings.pending_earnings
    verified_earnings = earnings.verified_earnings
    disapproved_earnings = earnings.disapproved_earnings
    withdrawn_earnings = earnings.withdrawn_earnings
    paid_earnings = earnings.paid_earnings

    task_items = worker.taskitems.all().exclude(ignored=True).values('unique_code')
    tasks = Task.objects.all().exclude(active=False).exclude(unique_code__in=task_items)
    pending_tasks = worker.taskitems.filter(pending=True).order_by('-date_performed')
    verified_tasks = worker.taskitems.filter(completed=True).order_by('-date_performed')
    disapproved_tasks = worker.taskitems.filter(disapproved=True).order_by('-date_performed')
    unattempted_tasks = Task.objects.all().exclude(active=False).exclude(unique_code__in=task_items).order_by('-date_created')
    total_tasks = tasks.count() + pending_tasks.count() + verified_tasks.count() + disapproved_tasks.count()
    
    context = {'domain':get_current_site(request), 'paid_earnings':paid_earnings, 'unattempted_tasks':unattempted_tasks, 'worker':worker, 'earnings_total':earnings_total, 'pending_earnings':pending_earnings, 'verified_earnings':verified_earnings, 'withdrawn_earnings':withdrawn_earnings, 'disapproved_earnings':disapproved_earnings, 'total_tasks': total_tasks, 'verified_tasks':verified_tasks, 'pending_tasks':pending_tasks, 'disapproved_tasks':disapproved_tasks}
    return render(request, 'task/profile.html', context)

@login_required(login_url='login')
def save_profile_form(request, form, template_name, ):
    data = dict()
    if request.method == 'POST':
        if form.is_valid():
            user = request.user
            form.save()
            user.full_name = request.POST.get('full_name')
            user.save()
            data['form_is_valid'] = True
            worker = user.worker
            data['html_profile_list'] = render_to_string('task/profile_list.html', {
                'worker': worker, 'user':user
            })
        else:
            data['form_is_valid'] = False

    context = {'form':form}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)          

@login_required(login_url='login')
def profile_edit(request):
    user = request.user

    worker = Worker.objects.get(user=user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=worker)

    else:
        form = ProfileForm(instance=worker)

    return save_profile_form(request, form, 'task/profile_edit.html')

@login_required(login_url='login')
def withdrawal(request):

    worker = request.user.worker
    earnings_total = Earnings.objects.get(worker=worker).get_total_earnings
    pending_earnings = Earnings.objects.get(worker=worker).pending_earnings
    verified_earnings = Earnings.objects.get(worker=worker).verified_earnings
    disapproved_earnings = Earnings.objects.get(worker=worker).disapproved_earnings
    withdrawn_earnings = Earnings.objects.get(worker=worker).withdrawn_earnings
    paid_earnings = Earnings.objects.get(worker=worker).paid_earnings
    
    form = WithdrawalForm()
    form2 = ComplainForm()
    if request.method == 'POST':
        try:
            if request.POST['text']:
                form2 = ComplainForm(request.POST)
                if form2.is_valid():
                    instance = form2.save(commit=False)
                    instance.worker = worker
                    instance.save()
                    sweetify.success(request, title='Message Received', text='We\'ll get back to you shortly', icon='success', button='Ok', timer=4500, extra_tags='complaint')
                    return redirect('withdrawal')
        except:
            form = WithdrawalForm(request.POST)
            if form.is_valid():
                worker = worker
                staffs = Worker.objects.filter(user__is_staff=True)
                paypal_address = worker.paypal_address
                amount_withdraw = Earnings.objects.get(worker=worker).verified_earnings
                withdrawal_request = Withdrawal.objects.create(worker=worker, paypal_address=paypal_address, amount_withdraw=amount_withdraw)
                withdrawal_request.save()
                sweetify.success(request, title='Request Sent', text='We\'ve received your message. You\'ll be paid shortly', icon='success', button='Ok', timer=4000, extra_tags='withdrawal')
                earning = Earnings.objects.get(worker=worker)
                earning.verified_earnings = '0'
                earning.withdrawn_earnings = verified_earnings + withdrawn_earnings
                earning.save()
                notification = Notification.objects.create(notification_type = 9, to_worker=earning.worker, earning=earning, withdrawal=withdrawal_request)
                with transaction.atomic():
                    for staff in staffs:
                        notification2 = Notification.objects.create(notification_type = 9, admin=staff, earning=earning, withdrawal=withdrawal_request)
                return redirect('withdrawal')
        
    context = {'paid_earnings':paid_earnings, 'form':form, 'form2':form2, 'worker':worker, 'earnings_total':earnings_total, 'pending_earnings':pending_earnings, 'verified_earnings':verified_earnings, 'withdrawn_earnings':withdrawn_earnings, 'disapproved_earnings':disapproved_earnings}
    return render(request, 'task/withdrawal.html', context)
login_required(login_url='login')
def helpcentre(request):
    worker = request.user.worker
    about = About.objects.all()    
    form = ComplainForm()
    if request.method == 'POST':
        form = ComplainForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.worker = worker
            instance.save()
            sweetify.success(request, title='Message Received', text='We\'ll get back to you shortly', icon='success', button='Ok', timer=4500)
            return redirect('help_centre')

    context = {'about':about, 'form':form}
    return render(request, 'task/helpcentre.html', context)

def terms(request):
    terms = Faqs_Terms.objects.exclude(faqs_title__isnull=False, faqs_text__isnull=False)

    form = SuscribersForm()

    if request.method == 'POST':
        form = SuscribersForm(request.POST)
        if form.is_valid():
            form.save()
            sweetify.success(request, title='Email Received', text='You have successfully suscribed to our newsletter', icon='success', button='Ok', extra_tags='newsletter')
            return redirect('terms')
        else:
            sweetify.error(request, title='Error',
                           text = '{}'.format(form.errors['email'].as_text()),
                           icon='error', button='Ok', extra_tags='contact')
            return redirect('terms')

    context = {'terms':terms, 'form':form}
    return render(request, 'task/terms.html', context)

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
#--------ADMIN STUFFS -------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

# DASHBOARD TASKS AND USERS LISTS AND DETAIL
@admin_only
def dashboard(request):

    tasks = Task.objects.all().exclude(active=False).order_by('-date_created')
    workers = Worker.objects.all().order_by('-date_created')[:15]

    total_tasks = tasks.count()
    verified_tasks = TaskItem.objects.filter(completed=True).exclude(ignored=True)
    pending_tasks = TaskItem.objects.filter(pending=True).exclude(ignored=True)[:15]
    disapproved_tasks = TaskItem.objects.filter(disapproved=True).exclude(ignored=True)
    unattempted_tasks = Task.objects.filter(taskitems__isnull=True).exclude(active=False)

    context = {'unattempted_tasks':unattempted_tasks, 'tasks':tasks, 'workers': workers, 'total_tasks':total_tasks, 'verified_tasks':verified_tasks, 'pending_tasks':pending_tasks, 'disapproved_tasks':disapproved_tasks}
    return render(request, 'task/dashboard.html', context)

@admin_only
def workers(request):
    workers = Worker.objects.all().order_by('-date_created')
    context = {'workers':workers}
    return render(request, 'task/workers.html', context)

@admin_only
def worker(request, pk_test):
    worker = Worker.objects.get(id=pk_test)

    pending_tasks = worker.taskitems.filter(pending=True)
    verified_tasks = worker.taskitems.filter(completed=True).exclude(ignored=True)
    disapproved_tasks = worker.taskitems.filter(disapproved=True).exclude(ignored=True)
    task_items = worker.taskitems.all().exclude(ignored=True).values('unique_code')
    task_items2 = worker.taskitems.filter(pending=True).exclude(ignored=True)
    unattempted_tasks = Task.objects.filter(active=True).exclude(unique_code__in=task_items).order_by('-date_created')

    earnings_total = Earnings.objects.get(worker=worker).get_total_earnings
    pending_earnings = Earnings.objects.get(worker=worker).pending_earnings
    verified_earnings = Earnings.objects.get(worker=worker).verified_earnings
    disapproved_earnings = Earnings.objects.get(worker=worker).disapproved_earnings
    withdrawn_earnings = Earnings.objects.get(worker=worker).withdrawn_earnings
    paid_earnings = Earnings.objects.get(worker=worker).paid_earnings
    total_tasks = unattempted_tasks.count() + pending_tasks.count() + verified_tasks.count() + disapproved_tasks.count()

    context = {'total_tasks':total_tasks, 'task_items':task_items2, 'domain':get_current_site(request), 'paid_earnings':paid_earnings, 'unattempted_tasks':unattempted_tasks, 'worker':worker, 'pending_tasks':pending_tasks, 'disapproved_tasks':disapproved_tasks, 'verified_tasks':verified_tasks, 'earnings_total':earnings_total, 'pending_earnings':pending_earnings, 'verified_earnings':verified_earnings, 'withdrawn_earnings':withdrawn_earnings, 'disapproved_earnings':disapproved_earnings}
    return render(request, 'task/workers_id.html', context)
@admin_only
def tasks(request):

    tasks = Task.objects.all().order_by('-date_created')

    context = {'tasks':tasks}
    return render(request, 'task/tasks.html', context)

@admin_only
def pending_tasks(request):
    tasks = TaskItem.objects.filter(pending=True).exclude(ignored=True).order_by('-date_performed')
    context = {'tasks':tasks}
    return render(request, 'task/pending_tasks.html', context)

@admin_only
def verified_tasks(request):
    tasks = TaskItem.objects.filter(completed=True).exclude(ignored=True).order_by('-date_performed')
    context = {'tasks':tasks}
    return render(request, 'task/verified_tasks.html', context)

@admin_only
def disapproved_tasks(request):
    tasks = TaskItem.objects.filter(disapproved=True).exclude(ignored=True).order_by('-date_performed')
    context = {'tasks':tasks}
    return render(request, 'task/disapproved_tasks.html', context)
#-----------------------------

#TASK CRUD
@admin_only
def save_task_form(request, form, template_name):
    data = dict()
    if request.method == 'POST':
        if form.is_valid():
            category = request.POST.get('category')
            category_2 = request.POST.get('category_2')
            description = request.POST.get('description')
            price = request.POST.get('price')
            link = request.POST.get('link')
            task_expiry_date = request.POST.get('task_expiry_date')
            task_expiry_time = request.POST.get('task_expiry_time')
            print(task_expiry_date)
            

            workers = Worker.objects.all().exclude(user__is_staff=True)
        
            print(request.path)
            if request.path == "/create_task/":
                task = Task.objects.create(category=category, category_2=category_2, description=description, price=price, link=link, task_expiry_date=task_expiry_date, task_expiry_time=task_expiry_time)
                task.save()
                with transaction.atomic():
                    for worker in workers:
                        notification = Notification.objects.create(notification_type = 2, to_worker=worker)
            else:
                task_obj = Task.objects.filter(id=form.pk)
                task = task_obj.update(category=category, category_2=category_2, description=description, price=price, link=link, task_expiry_date=task_expiry_date, task_expiry_time=task_expiry_time, who_updated=request.user.full_name)
                with transaction.atomic():
                    for worker in workers:
                        try:
                            task_object = worker.taskitems.get(unique_code=task_obj.unique_code).exclude(ignored=True)
                            if task_object.pending == True:
                                notification = Notification.objects.create(notification_type = 3, to_worker=worker, task=task_object)
                        except:
                            pass
            data['form_is_valid'] = True
            tasks = Task.objects.all().order_by('-date_created')
            data['html_task_list'] = render_to_string('task/partial_task_list.html', {
                'tasks': tasks
            })
        else:
            data['form_is_valid'] = False

    context = {'form':form}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)

@admin_only
def createTask(request):

    if request.method == 'POST':
        form = TaskForm(request.POST)
    else:
        form = TaskForm()

    return save_task_form(request, form, 'task/partial_task_create.html')

@admin_only
def updateTask(request, pk):

    task = get_object_or_404(Task, id=pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)

    else:
        form = TaskForm(instance=task)
    return save_task_form(request, form, 'task/partial_task_update.html')

@admin_only
def deleteTask(request, pk):
    task = get_object_or_404(Task, id=pk)
    data = dict()
    if request.method == 'POST':
        task.delete()

        data['form_is_valid'] = True
        tasks = Task.objects.all()
        data['html_task_list'] = render_to_string('task/partial_task_list.html', {'tasks':tasks})
    else:
        context = {'task':task}
        data['html_form'] = render_to_string('task/partial_task_delete.html', context, request=request)
    return JsonResponse(data)
#-----------------------------

#TASK STATUS UPDATE
@csrf_exempt
@admin_only
def verify_task(request, task_pk):

    try:
        task = TaskItem.objects.filter(pending=True).get(id=task_pk)
        task.completed = True
        task.pending = False
        task.disapproved = False
        task.save()
        verified_earnings = Earnings.objects.get(worker=task.worker).verified_earnings
        pending_earnings = Earnings.objects.get(worker=task.worker).pending_earnings
        earning = Earnings.objects.get(worker=task.worker)
        earning.verified_earnings = verified_earnings + task.task.price
        earning.pending_earnings = pending_earnings - task.task.price
        earning.save()
        notification = Notification.objects.create(notification_type = 5, to_worker=task.worker, task=task, earning=earning)
    except:
        task = TaskItem.objects.filter(disapproved=True).get(id=task_pk)
        task.completed = True
        task.pending = False
        task.disapproved = False
        task.save()
        verified_earnings = Earnings.objects.get(worker=task.worker).verified_earnings
        disapproved_earnings = Earnings.objects.get(worker=task.worker).disapproved_earnings
        earning = Earnings.objects.get(worker=task.worker)
        earning.verified_earnings = verified_earnings + task.task.price 
        earning.disapproved_earnings = disapproved_earnings - task.task.price
        earning.save()
        notification = Notification.objects.create(notification_type = 6, to_worker=task.worker, task=task, earning=earning)
    return redirect(request.META['HTTP_REFERER'])

@csrf_exempt
@admin_only
def disapprove_task(request, task_pk):
    try:
        task = TaskItem.objects.filter(pending=True).get(id=task_pk)
        task.completed = False
        task.pending = False
        task.disapproved = True
        task.save()
        pending_earnings = Earnings.objects.get(worker=task.worker).pending_earnings
        disapproved_earnings = Earnings.objects.get(worker=task.worker).disapproved_earnings
        earning = Earnings.objects.get(worker=task.worker)
        earning.disapproved_earnings = disapproved_earnings + task.task.price
        earning.pending_earnings = pending_earnings - task.task.price
        earning.save()
        notification = Notification.objects.create(notification_type = 7, to_worker=task.worker, task=task, earning=earning)
    except:
        task = TaskItem.objects.filter(completed=True).get(id=task_pk)
        task.completed = False
        task.pending = False
        task.disapproved = True
        task.save()
        verified_earnings = Earnings.objects.get(worker=task.worker).verified_earnings
        disapproved_earnings = Earnings.objects.get(worker=task.worker).disapproved_earnings
        earning = Earnings.objects.get(worker=task.worker)
        earning.disapproved_earnings = disapproved_earnings + task.task.price
        earning.verified_earnings = verified_earnings - task.task.price
        earning.save()
        notification = Notification.objects.create(notification_type = 8, to_worker=task.worker, task=task, earning=earning)

    return redirect(request.META['HTTP_REFERER'])
#-----------------------------

#PAYMENTS AND WITHDRAWAL STUFFS
@admin_only
def withdrawalrequests(request):
    withdrawalrequests = Withdrawal.objects.all()[:12]

    context = {'withdrawalrequests':withdrawalrequests}
    return render(request, 'task/withdrawalrequests.html', context)

@admin_only
def pending_withdrawalrequests(request):
    withdrawalrequests = Withdrawal.objects.filter(verified=False)

    context = {'withdrawalrequests':withdrawalrequests}
    return render(request, 'task/pending_withdrawalrequests.html', context)

@admin_only
def verified_withdrawalrequests(request):
    withdrawalrequests = Withdrawal.objects.filter(verified=True)

    context = {'withdrawalrequests':withdrawalrequests}
    return render(request, 'task/verified_withdrawalrequests.html', context)

@admin_only
def approvewithdrawalrequests(request, withdrawal_pk):
    withdrawalrequest = Withdrawal.objects.filter(verified=False).get(id=withdrawal_pk)
    withdrawalrequest.verified = True
    paid_earnings = Earnings.objects.get(worker=withdrawalrequest.worker).paid_earnings
    withdrawn_earnings = Earnings.objects.get(worker=withdrawalrequest.worker).withdrawn_earnings
    earning = Earnings.objects.get(worker=withdrawalrequest.worker)
    earning.paid_earnings = paid_earnings + withdrawn_earnings
    earning.withdrawn_earnings = "0"
    earning.save()
    withdrawalrequest.save()
    notification = Notification.objects.create(notification_type = 10, to_worker=earning.worker, earning=earning, withdrawal=withdrawalrequest)
    
    sweetify.success(request, title='Verified', text='The Payment has been verified', icon='success', button='Ok', timer=3000)
    return redirect(request.META['HTTP_REFERER'])
#-----------------------------

#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------------
#---------------------USER STUFFS --------------------------------------------------------------
#-------------------------------------------------------------------------------------------------

#DASHBOARD AND TASKS LISTS
@login_required(login_url='login')
def userPage(request):
    task_items = request.user.worker.taskitems.all().values('unique_code')
    profile_task = Task.objects.filter(active=True, category_2='Profile').exclude(unique_code__in=task_items)
    all_tasks = Task.objects.filter(active=True).exclude(unique_code__in=task_items).exclude(category_2='Profile').order_by('-updated')
    tasks = chain(profile_task, all_tasks)
    verified_tasks = request.user.worker.taskitems.filter(completed=True).order_by('-date_performed')
    pending_tasks = request.user.worker.taskitems.filter(pending=True).order_by('-date_performed')
    disapproved_tasks = request.user.worker.taskitems.filter(disapproved=True).order_by('-date_performed')
    unattempted_tasks = Task.objects.filter(active=True).exclude(unique_code__in=task_items).order_by('-date_created')
    total_tasks = all_tasks.count() + profile_task.count() + pending_tasks.count() + verified_tasks.count() + disapproved_tasks.count()
    new_tasks = all_tasks.count() + profile_task.count()
    context = {'new_tasks':new_tasks, 'unattempted_tasks':unattempted_tasks, 'tasks':tasks, 'total_tasks': total_tasks, 'verified_tasks':verified_tasks, 'pending_tasks':pending_tasks, 'disapproved_tasks':disapproved_tasks }
    return render(request, 'task/userpage.html', context)

def unattemptedtask(request):
    task_items = request.user.worker.taskitems.all().exclude(ignored=True).values('unique_code')
    worker = request.user.worker
    profile_task = Task.objects.filter(active=True, category_2='Profile').exclude(unique_code__in=task_items)
    tasks = Task.objects.filter(active=True).exclude(unique_code__in=task_items).exclude(category_2='Profile').order_by('-date_created')
    unattemptedtasks = chain(profile_task, tasks)
    context = {'unattempted_tasks':unattemptedtasks}
    return render(request, 'task/unattemptedtasks.html', context)

def worker_pending_tasks(request):
    worker = request.user.worker
    worker_pending_tasks = worker.taskitems.filter(pending=True).order_by('-date_performed')

    context = {'worker_pending_tasks':worker_pending_tasks}
    return render(request, 'task/worker_pending_tasks.html', context)

def worker_verified_tasks(request):
    worker = request.user.worker
    worker_verified_tasks = worker.taskitems.filter(completed=True).order_by('-date_performed')

    context = {'worker_verified_tasks':worker_verified_tasks}
    return render(request, 'task/worker_verified_tasks.html', context)

def worker_disapproved_tasks(request):
    worker = request.user.worker
    worker_disapproved_tasks = worker.taskitems.filter(disapproved=True).order_by('-date_performed')

    context = {'worker_disapproved_tasks':worker_disapproved_tasks}
    return render(request, 'task/worker_disapproved_tasks.html', context)
#----------------------------------------------------------------------------------------------

#TASKS STATUS UPDATE
@login_required(login_url='login')
def deleteYourTask(request, pk):
    task_items = request.user.worker.taskitems.all().exclude(ignored=True).values('unique_code')
    task = Task.objects.exclude(unique_code__in=task_items).exclude(active=False).get(id=pk)

    TaskItem.objects.create(task=task, worker=request.user.worker, pending=False, ignored=True, unique_code=task.unique_code)

    sweetify.success(request, title='Done', text='Task has been ignored', icon='success', button='Ok', timer=3000)
    return redirect(request.META['HTTP_REFERER'])

@login_required(login_url='login')
def attemptTask(request, pk):
    task_items = request.user.worker.taskitems.all().exclude(ignored=True).values('unique_code')
    task = Task.objects.exclude(unique_code__in=task_items).get(id=pk)
    pending_earnings = Earnings.objects.get(worker=request.user.worker).pending_earnings
    staffs = Worker.objects.filter(user__is_staff=True)
    if request.method == 'POST':
        task = Task.objects.exclude(unique_code__in=task_items).exclude(active=False).get(id=pk)
        task_item = TaskItem.objects.create(task=task, worker=request.user.worker, ignored=False, unique_code=task.unique_code, pending=True, completed=False, disapproved=False)
        earning = Earnings.objects.get(worker=request.user.worker)
        earning.pending_earnings = pending_earnings + task.price
        earning.save()
        notification = Notification.objects.create(notification_type = 4, to_worker=task.worker, task=task_item, earning=earning)
        with transaction.atomic():
            for staff in staffs:
                notification2 = Notification.objects.create(notification_type = 4, admin=staff, task=task_item, earning=earning)

    return JsonResponse({'pending':task_item.pending})
#----------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------
#---------ALL NOTIFICATIONS VIEW-------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------

class RemoveNotification(LoginRequiredMixin, View):
    def delete(self, request, notification_pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)
        except:
            notification = Notification.objects.get(admin=request.user.worker, id=notification_pk)
        notification.worker_has_seen = True
        notification.save()

        return HttpResponse('Success', content_type='text/plain')

class MarkReadView(LoginRequiredMixin, View):
    def delete(self, request, *args, **kwargs):
        if request.user.is_staff:
            notifications = Notification.objects.filter(admin=request.user.worker).exclude(worker_has_seen=True)
            notifications.update(worker_has_seen=True)
        else:
            notifications = Notification.objects.filter(to_worker=request.user.worker).exclude(worker_has_seen=True)
            notifications.update(worker_has_seen=True)
        
        return HttpResponse('Success', content_type='text/plain')

# ADMIN NOTIFICATIONS

class NewWorkerNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        admin = Worker.objects.filter(user__is_staff=True).get(user=request.user)
        notification = Notification.objects.get(admin=admin, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('tasks')

class PendingTaskAdminNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        admin = Worker.objects.filter(user__is_staff=True).get(user=request.user)
        notification = Notification.objects.get(admin=admin, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('pending_tasks')

class WithdrawalRequestAdminNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        admin = Worker.objects.filter(user__is_staff=True).get(user=request.user)
        notification = Notification.objects.get(admin=admin, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('withdrawalrequests')

#--------------------------

# WORKERS NOTIFICATIONS

class WelcomeNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('terms')

class ReferralNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)
        except:
            notification = Notification.objects.get(admin=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('/withdrawal/#earnings-verified')

class TaskNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('unattempted_tasks')

class TaskUpdateNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()
        task_id = notification.task.id

        return redirect("/worker_pending_tasks/#pending-task-{}".format(task_id))

class TaskAttemptNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('worker_pending_tasks')

class TaskVerifiedNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('worker_verified_tasks')

class TaskDisapproveNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('worker_disapproved_tasks')

class WithdrawalRequestNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('/withdrawal/#earnings-requested')

class WithdrawalEarningsPaidNotification(LoginRequiredMixin, View):
    def get(self, request, notification_pk, *args, **kwargs):
        notification = Notification.objects.get(to_worker=request.user.worker, id=notification_pk)

        notification.worker_has_seen = True
        notification.save()

        return redirect('/withdrawal/#earnings-paid')

#--------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------

def handler404(request, exception=None):
    sweetify.error(request, title='Sorry', text='That page you were looking for does not exist', icon='error', button='Ok', timer=4000)
    return redirect('/', status=404)

def handler500(request):
    sweetify.error(request, title='Sorry', text='Something went wrong, Try again later', icon='error', button='Ok', timer=4000)
    return redirect('/', status=500)
