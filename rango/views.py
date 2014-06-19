from django.shortcuts import render_to_response
from datetime import datetime
# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm

from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
####
#Global utility
def get_category_list():
    category_list = Category.objects.all()
    for category in category_list:
        category.url = category.name.replace(' ','_')

    return category_list
####
def decode_url(name_url):
    if name_url.find(' '):
        return name_url.replace(' ','_')
    elif name_url.find('_'):
        return name_url.replace('_',' ')
def index(request):
    request.session.set_test_cookie()
    context       = RequestContext(request)

    category_list = get_category_list()

    page_list     = Page.objects.order_by('-views')[:5]
    context_dict  = {'categories':category_list,
                     'pages':page_list}

    #print category_list
    #for category in category_list:
    #    category.url = category.name.replace(' ','_')
        #category.url = decode_url(category.name)

    #### NEW CODE ####
    # Obtain our Response object early so we can add cookie information.
    #response = render_to_response('rango/index.html', context_dict, context)

    

    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    context = RequestContext(request)
    context_dict = {'name':"ASka dfhf"}
    #add categories to sidebar
    
    category_list = get_category_list()

    context['categories'] = category_list

    response = render_to_response('rango/about.html', context_dict, context)

    if 'last_visit' in request.COOKIES:
        # Yes it does! Get the cookie's value.
        last_visit = request.COOKIES['last_visit']
        # Cast the value to a Python date/time object.
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        # If it's been more than a day since the last visit...
        if (datetime.now() - last_visit_time).days > 0:
            # ...reassign the value of the cookie to +1 of what it was before...
            response.set_cookie('visits', visits+1)
            # ...and update the last visit cookie, too.
            response.set_cookie('last_visit', datetime.now())
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        response.set_cookie('last_visit', datetime.now())

    return response

def category(request, category_name_url):
    context = RequestContext(request)
    
    #decode parameter from url
    category_name = category_name_url.replace('_',' ')
    category_list = get_category_list()
    context_dict = {'category_name':category_name,'categories':category_list}
    try:
        category = Category.objects.get(name=category_name)
        pages    = Page.objects.filter(category=category)
        
        # ORM objects
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
    return render_to_response('rango/category.html',context_dict,context)


@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method =='GET':
        cat_id = request.GET['category_id']
    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
            category.save()
    return HttpResponse(likes)


def add_category(request):
    context = RequestContext(request)

    category_list = get_category_list()
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)

            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()
    return render_to_response('rango/add_category.html',{'form':form,'categories':category_list},context)

def add_page(request,category_name_url):
    context = RequestContext(request)
    category_list = get_category_list()
    category_name = category_name_url.replace('_',' ')
    if request.method =='POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('/rango/add_category.html',{'categories':category_list},context)

            page.views = 0
            page.save()
            return category(request,category_name_url)
        else:
            print form.errors
    else:
        # create a empty form 
        form = PageForm()
    return render_to_response('rango/add_page.html',
                              {'category_name_url':category_name_url,
                              'category_name':category_name,
                              'categories':category_list,
                              'form':form},
                              context)


def register(request):
    request.session.set_test_cookie()
    if request.session.test_cookie_worked():
        print ">>> TEST COOKIE WORKED"
        request.session.delete_test_cookie()
    context = RequestContext(request)
    category_list = get_category_list()

    registered = False
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form    = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()
            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
        else:
            # Invalid form or forms - mistakes or something else?
            # Print problems to the terminal.
            # They'll also be shown to the user.
            print user_form.errors , profile_form.errors
    else:
        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response('rango/register.html',
                             {'user_form': user_form, 'profile_form': profile_form, 'registered': registered,'categories':category_list},
                              context)

def user_login(request):
    context = RequestContext(request)
    category_list = get_category_list()

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request,user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse('Your Rango account is disabled.')
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse('Invalid login details')
    else:
        # The request is not a HTTP POST, so display the login form.
        # This scenario would most likely be a HTTP GET.
        return render_to_response('rango/login.html',{'categories':category_list},context)

@login_required
def user_profile(request):
    context = RequestContext(request)
    category_list = get_category_list()

    context_dict = {'categories':category_list}
    try:
        uprofile = UserProfile.objects.get(user=request.user)
    except:
        uprofile = None
    context_dict['userprofile'] = uprofile

 
    return render_to_response('rango/profile.html',context_dict,context)

@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/rango/')

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except :
                pass
    return redirect(url)