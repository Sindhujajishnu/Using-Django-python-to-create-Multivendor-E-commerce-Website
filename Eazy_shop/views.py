from django.http import JsonResponse
from django.shortcuts import redirect, render
from shop.form import CustomUserForm, ChatMessageForm
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models import Q
import json


def home(request):
    products = Product.objects.filter(trending=1)
    return render(request, "shop/index.html", {"products": products})


def favviewpage(request):
    if request.user.is_authenticated:
        fav = Favourite.objects.filter(user=request.user)
        return render(request, "shop/fav.html", {"fav": fav})
    else:
        return redirect("/")


def remove_fav(request, fid):
    item = Favourite.objects.get(id=fid)
    item.delete()
    return redirect("/favviewpage")


def cart_page(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
        return render(request, "shop/cart.html", {"cart": cart})
    else:
        return redirect("/")


def remove_cart(request, cid):
    cartitem = Cart.objects.get(id=cid)
    cartitem.delete()
    return redirect("/cart")


def fav_page(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.load(request)
            product_id = data['pid']
            product_status = Product.objects.get(id=product_id)
            if product_status:
                if Favourite.objects.filter(user=request.user.id, product_id=product_id):
                    return JsonResponse({'status': 'Product Already in Favourite'}, status=200)
                else:
                    Favourite.objects.create(user=request.user, product_id=product_id)
                    return JsonResponse({'status': 'Product Added to Favourite'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Favourite'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)


def add_to_cart(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.load(request)
            product_qty = data['product_qty']
            product_id = data['pid']
            # print(request.user.id)
            product_status = Product.objects.get(id=product_id)
            if product_status:
                if Cart.objects.filter(user=request.user.id, product_id=product_id):
                    return JsonResponse({'status': 'Product Already in Cart'}, status=200)
                else:
                    if product_status.quantity >= product_qty:
                        Cart.objects.create(user=request.user, product_id=product_id, product_qty=product_qty)
                        return JsonResponse({'status': 'Product Added to Cart'}, status=200)
                    else:
                        return JsonResponse({'status': 'Product Stock Not Available'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Cart'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)


def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out Successfully")
    return redirect("/login")


def login_page(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        if request.method == 'POST':
            name = request.POST.get('username')
            pwd = request.POST.get('password')
            user = authenticate(request, username=name, password=pwd)
            if user is not None:
                login(request, user)
                # messages.success(request, "Logged in Successfully")
                return redirect("/")
            else:
                messages.error(request, "Invalid User Name or Password")
                return redirect("/login")
        return render(request, "shop/login.html")


def register(request):
    form = CustomUserForm()
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration Success You can Login Now..!")
            return redirect('/login')
    return render(request, "shop/register.html", {'form': form})


def collections(request):
    catagory = Catagory.objects.filter(status=1)
    return render(request, "shop/collections.html", {"catagory": catagory})


def collectionsview(request, name):
    if (Catagory.objects.filter(name=name, status=1)):
        products = Product.objects.filter(category__name=name)
        return render(request, "shop/products/index.html", {"products": products, "category_name": name})
    else:
        messages.warning(request, "No Such Catagory Found")
        return redirect('collections')


def product_details(request, cname, pname):
    if (Catagory.objects.filter(name=cname, status=1)):
        if (Product.objects.filter(name=pname, status=1)):
            products = Product.objects.filter(name=pname, status=1).first()
            pro_vendor_details = Vendor.objects.filter(id=products.vendor_id).first()
            # print(pro_vendor_details.email)
            vendor_details = User.objects.filter(email=pro_vendor_details.email).first()
            # print(vendor_details.id)
            return render(request, "shop/products/product_details.html",
                          {"products": products, "id": vendor_details.id})
        else:
            messages.error(request, "No Such Produtct Found")
            return redirect('collections')
    else:
        messages.error(request, "No Such Catagory Found")
        return redirect('collections')


def getUserDetails(request):
    if request.user.is_staff: #vendor
        user_qs = User.objects.filter(is_staff=False, is_superuser=False) #customr
    else:
        user_qs = User.objects.filter(is_staff=True, is_superuser=False) #vendor

    # get the IDs of all currently logged-in users
    online_user_ids = []
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        online_user_ids.append(int(data.get('_auth_user_id', None)))
    # create the user data list, including online/offline status
    all_user_data = []
    for user in user_qs:
        status = 'online' if user.id in online_user_ids else 'offline'
        user_data = {'id': user.id, 'username': user.username, 'is_staff': user.is_staff,
                     'is_superuser': user.is_superuser, 'status': status, 'first_name': user.first_name,
                     'last_name': user.last_name, 'msg': newMessageCount(user.id, request.user.id)}
        all_user_data.append(user_data)
    return JsonResponse(all_user_data, safe=False)


def newMessageCount(friend_id, user_id):
    chats = ChatMessage.objects.filter(msg_sender__id=friend_id, msg_receiver=user_id, seen=False)
    return chats.count()


def active_users_view(request):
    if request.user.is_authenticated:
        return render(request, 'shop/active_users.html')
    else:
        messages.error(request, "Login Here to Access")
        return redirect('/login')


def viewChat(request, pk):
    if request.user.is_authenticated:
        friend_user = User.objects.filter(id=pk)
        friend_details = [{'id': user.id, 'username': user.username, 'is_staff': user.is_staff,
                           'is_superuser': user.is_superuser, 'first_name': user.first_name,
                           'last_name': user.last_name} for user in friend_user]
        current_user = request.user.id
        frd_id = friend_details[0]["id"]

        form = ChatMessageForm()
        if request.method == 'POST':
            form = CustomUserForm(request.POST)
            if form.is_valid():
                chat_message = form.save(commit=False)
                data = json.loads(request.body)
                chat_message.body = data["msg"]
                print(chat_message)
                chat_message.msg_sender = current_user
                chat_message.msg_receiver = frd_id
                chat_message.seen = False
                chat_message.save()

        rec_chats = ChatMessage.objects.filter(
            Q(msg_sender=frd_id, msg_receiver=current_user) | Q(msg_sender=current_user, msg_receiver=frd_id))

        update_rec_chats = ChatMessage.objects.filter(msg_sender=frd_id, msg_receiver=current_user, seen=False)
        print(update_rec_chats)
        update_rec_chats.update(seen=True)

        return render(request, 'shop/viewChat.html',
                      {"user_details": friend_details[0], "messages": rec_chats, 'form': form,
                       "num": rec_chats.count()})
    else:
        messages.error(request, "Login Here to Access")
        return redirect('/login')


def sentMessages(request, pk):
    online_user_ids = []
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        online_user_ids.append(int(data.get('_auth_user_id', None)))
    # print(online_user_ids)
    user = request.user
    profile = User.objects.filter(id=pk).first()
    data = json.loads(request.body)
    new_chat = data["msg"]
    status = True if profile.id in online_user_ids else False
    print("Status  : ", status)
    new_chat_message = ChatMessage.objects.create(body=new_chat, msg_sender=user, msg_receiver=profile, seen=False)
    # print(new_chat)
    return JsonResponse(new_chat_message.body, safe=False)


def getMessages(request, pk):
    rec_chats = {"error": "Null"}
    if request.user.is_authenticated:
        friend_user = User.objects.filter(id=pk)
        friend_details = [{'id': user.id, 'username': user.username, 'is_staff': user.is_staff,
                           'is_superuser': user.is_superuser, 'first_name': user.first_name,
                           'last_name': user.last_name} for user in friend_user]
        current_user = request.user.id
        frd_id = friend_details[0]["id"]
        messages = ChatMessage.objects.filter(
            Q(msg_sender=frd_id, msg_receiver=current_user) | Q(msg_sender=current_user, msg_receiver=frd_id))
        rec_chats = [{'msg': msg.body, 'msg_sender': msg.msg_sender_id, 'msg_receiver': msg.msg_receiver_id} for msg in
                     messages]
    return JsonResponse(rec_chats, safe=False)
