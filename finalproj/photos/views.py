from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.template import RequestContext, loader
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from lib.utils import filter_session, clean_session
from .forms import UserForm
from django.db.utils import IntegrityError
from datetime import datetime
from lib import utils, aws_utils, constants
from .models import Photos

import hashlib
import json
import traceback
from datetime import datetime


# Create your views here.
def index(request):
    photos = fetch_photos()
    return render_to_response('photos_base.html',
            {
                "actual_page": "photos_index.html",
                "session_info": filter_session(request.session),
                "photos": json.dumps(photos),
            },
            RequestContext(request))

@csrf_exempt
def register(request):
    error_msg = None
    if request.method == 'POST':
        data = request.POST
        usrform = UserForm(request.POST)
        if usrform.is_valid():
            data = usrform.cleaned_data
            try:
                user = User.objects.get(email=data['email'])
                error_msg = "Email %s has already been used." % (data['email'])
            except ObjectDoesNotExist as e:
                user = User.objects.create_user(data['email'], data['email'], data['auth'])
                user.first_name = data['firstname']
                user.last_name = data['lastname']
                user.is_active = 0
                user.save()
                aws_utils.put_subscriber_list(data['email'])
                aws_utils.subscribe_sns_topic(data['email'], data['email'])
                msg = "An AWS SNS confirmation email has been sent to %s. Please confirm and come back to sign in" % (data['email'])
                return render_to_response('photos_base.html',
                    {
                        "actual_page": "photos_signin.html",
                        "session_info": filter_session(request.session),
                        "error_message": msg,
                    },
                    RequestContext(request))
        else:
            error_msg = "Invalid registration information"

    return render_to_response('photos_base.html',
            {
                "actual_page": "photos_register.html",
                "session_info": filter_session(request.session),
                "error_message": error_msg,
            },
            RequestContext(request))

@csrf_exempt
def signin(request):
    error_message = None
    if request.method == "POST":
        data = request.POST
        user = authenticate(username=data.get('email'), password=data.get('auth'))
        if user is None:
            try:
                user = verify_user(data.get('email'))
            except Exception as e:
                user = None

        if user is not None:
            user.last_login = datetime.now()
            user.save()
            request.session['registered_first_name'] = user.first_name
            request.session['registered_last_name'] = user.last_name
            request.session['registered_email'] = user.email
            return redirect('/photos/')
        else:
            error_message = "Invalid username or password"

    return render_to_response('photos_base.html',
            {
                "actual_page": "photos_signin.html",
                "session_info": filter_session(request.session),
                "error_message": error_message,
            },
            RequestContext(request))

def verify_user(email):
    try:
        user = User.objects.get(email=email)
        subscriptions = aws_utils.list_subscriptions(email)
        if subscriptions[0]['SubscriptionArn'] == 'PendingConfirmation':
            return None
        user.is_active = 1
        user.save()
        return user
    except Exception as e:
        return None

def signout(request):
    clean_session(request.session)
    return redirect('/photos/')

@csrf_exempt
def upload(request):
    if request.method == "POST" and validate_upload_request(request):
        image_data = request.FILES['photo'].read()
        category = request.POST.get('category', '')
        description = request.POST.get('description', '')
        email = request.session['registered_email']
        user = User.objects.get(username=email)
        _user_hash = utils.user_hash(email)
        _image_hash = hashlib.md5(image_data).hexdigest()
        key = "%s/%s" % (_user_hash, _image_hash)
        s3 = aws_utils.get_s3_client()
        s3.put_object(Body=image_data,
                      Bucket=constants.S3_BUCKET,
                      Key=key,
                      ACL="public-read",
                      Metadata={
                          "owner_email":email,
                          "owner_name": user.first_name + " " + user.last_name})
        photo = Photos.objects.get_or_create(user=user, s3_key=key)[0]
        photo.description = description
        photo.category = category
        photo.save()
    return redirect("/photos/")


def validate_upload_request(request):
    if request.session.get('registered_email') is None:
        return False
    if request.FILES.get('photo') is None:
        return False
    return True


def fetch_photos(user_email=None, category=None):
    photos = Photos.objects.all()
    if user_email:
        user = User.objects.get(username=user_email)
        photos = photos.filter(user=user)
    if category:
        photos = photos.filter(category=category)
    ret = []
    for ph in photos:
        ret.append({
            'user_email': ph.user.email,
            'user_name': ph.user.first_name + " " + ph.user.last_name,
            'key': ph.s3_key,
            'category': ph.category,
            'description': ph.description,
            })
    return ret


def subscribe(request):
    subscriber = request.GET.get('subscriber');
    target = request.GET.get('target');
    try:
        if request.session.get('registered_email') is None:
            raise Exception("Not authorized")
        add_subscribe(subscriber, target);
        return JsonResponse({"result":"success"})
    except Exception as e:
        return JsonResponse({"result":"failed", "error": str(e)})


def add_subscribe(subscriber, target):
    if subscriber is None or target is None:
        raise ValueError("Invalid subscriber or target")
    aws_utils.update_subscription(subscriber, target)
