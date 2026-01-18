import datetime
from itertools import count
from werkzeug.security import check_password_hash,generate_password_hash

from bson import ObjectId
import os
from dns.e164 import query
from flask import Flask, request, render_template, redirect, session
import pymongo
from pyexpat.errors import messages

my_client =pymongo.MongoClient("mongodb://localhost:27017")
my_database = my_client["Restaurant_Food_Ordering_System"]

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PICTURE_PATH = APP_ROOT + "/static/picture"

admin_collection = my_database["Admin"]
customer_collection = my_database["Customer"]
delivery_boy_collection = my_database["Delivery_Boy"]
food_category_collection = my_database["Food_Category"]
locations_collection = my_database["Locations"]
menu_items_collection = my_database["Menu_Items"]
orders_collection = my_database["Orders"]
payments_collection = my_database["Payments"]
restaurant_collection = my_database["Restaurant"]

app = Flask(__name__)
app.secret_key = "restaurant_food_ordering_system"
admin_username = "admin"
admin_password = "admin"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")

@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == admin_username and password == admin_password :
        session["role"] = "Admin"
        return redirect("/admin_home")
    else :
        return render_template("message.html", message = "Invalid Login Details")

@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")

@app.route("/customer_login_action", methods=['post'])
def customer_login_action():
    email = request.form.get("email")
    password = request.form.get("password")

    query = {"email": email}
    customer = customer_collection.find_one(query)
    if customer and check_password_hash(customer['password'],password):
        customer = customer_collection.find_one(query)
        session['customer_id'] = str(customer['_id'])
        session['role'] = 'Customer'
        return redirect("/customer_home")
    else:
        return render_template("message.html", message="Invalid login Details")

@app.route("/customer_home")
def customer_home():
    return render_template("customer_home.html")

@app.route("/customer_registration")
def customer_registration():
    return render_template("customer_registration.html")

@app.route("/customer_registration_action", methods=['post'])
def customer_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    address = request.form.get("address")
    state = request.form.get("state")
    city = request.form.get("city")
    zip_code = request.form.get("zip_code")
    if password != confirm_password:
        return render_template("message.html", message="Password Not Matched")

    query = {"email": email}
    count = customer_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="Duplicate Email Address")

    query = {"phone": phone}
    count = customer_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="Duplicate Phone Number")
    hashed_password = generate_password_hash(password)
    query = {"first_name": first_name,"last_name": last_name, "email": email, "phone": phone, "password": hashed_password, "address": address, "state": state, "city": city, "zip_code": zip_code}
    customer_collection.insert_one(query)

    return render_template("message.html", message="Customer Registration Successful")

@app.route("/restaurant_login")
def restaurant_login():
    return render_template("restaurant_login.html")

@app.route("/restaurant_login_action", methods=['post'])
def restaurant_login_action():
    email = request.form.get('email')
    password = request.form.get('password')
    query = {"email": email}
    restaurant = restaurant_collection.find_one(query)
    if restaurant and check_password_hash(restaurant['password'],password):
        restaurant = restaurant_collection.find_one(query)
        session['restaurant_id'] = str(restaurant['_id'])
        if restaurant['status'] == "authorized":
            session['role'] = 'Restaurant'
            return render_template('restaurant_home.html')
        else:
            return render_template("message.html", message="You are not Authorized")
    else:
        return render_template('message.html', message='Invalid Login Details')


@app.route("/restaurant_registration")
def restaurant_registration():
    query = {}
    locations = list(locations_collection.find(query))
    return render_template("restaurant_registration.html",locations=locations)

@app.route("/restaurant_registration_action", methods=['post'])
def restaurant_registration_action():
    location_id = request.form.get("location_id")
    restaurant_name = request.form.get("restaurant_name")
    owner_first_name = request.form.get("owner_first_name")
    owner_last_name = request.form.get("owner_last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    dob = request.form.get("dob")
    ssn = request.form.get("ssn")
    address = request.form.get("address")
    status = request.form.get("status")

    if password != confirm_password:
        return render_template("message.html", message="Password Not Matched")

    query = {"email": email}
    count = restaurant_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="Email Already Registered")

    query = {"phone": phone}
    count = restaurant_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="Number Already Registered")
    hashed_password = generate_password_hash(password)
    query = {"restaurant_name": restaurant_name,"owner_first_name": owner_first_name, "owner_last_name":owner_last_name ,"email": email, "phone": phone, "password": hashed_password,"dob":dob,"ssn":ssn, "address": address, "status": 'unauthorized', "location_id":ObjectId(location_id)}
    restaurant_collection.insert_one(query)
    return render_template("message.html", message="Restaurant Registration successful")

@app.route("/authorize_restaurant")
def authorize_restaurant():
    restaurant_id = request.args.get("restaurant_id")
    query = {"_id": ObjectId(restaurant_id)}
    query1 = {"$set":{"status": "authorized"}}
    restaurant_collection.update_one(query,query1)
    return redirect("/view_restaurants")

@app.route("/unauthorize_restaurant")
def unauthorize_restaurant():
    restaurant_id = request.args.get("restaurant_id")
    query = {"_id": ObjectId(restaurant_id)}
    query1 = {"$set": {"status": "unauthorized"}}
    restaurant_collection.update_one(query, query1)
    return redirect("/view_restaurants")

@app.route("/restaurant_home")
def restaurant_home():
    return render_template("restaurant_home.html")

@app.route("/view_restaurants")
def view_restaurants():
    query = {}
    restaurants = restaurant_collection.find(query)
    restaurants = list(restaurants)
    return render_template("view_restaurants.html",restaurants=restaurants)

@app.route("/delivery_boy_login")
def delivery_boy_login():
    return render_template("delivery_boy_login.html")

@app.route("/delivery_boy_login_action", methods=['post'])
def delivery_boy_login_action():
    email = request.form.get('email')
    password = request.form.get('password')
    query = {"email": email}
    delivery_boy = delivery_boy_collection.find_one(query)
    if delivery_boy and check_password_hash(delivery_boy['password'],password):
        delivery_boy = delivery_boy_collection.find_one(query)
        session['delivery_boy_id'] = str(delivery_boy['_id'])
        if delivery_boy['status'] == "authorized":
            session['role'] = 'Delivery Boy'
            return render_template('delivery_boy_home.html')
        else:
            return render_template("message.html", message="You are not authorized")
    else:
        return render_template('message.html', message='Invalid Login Details')

@app.route("/delivery_boy_registration")
def delivery_boy_registration():
    return render_template("delivery_boy_registration.html")

@app.route("/delivery_boy_registration_action", methods=['post'])
def delivery_boy_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    dob = request.form.get("dob")
    ssn = request.form.get("ssn")
    address = request.form.get("address")
    state = request.form.get("state")
    city = request.form.get("city")
    zip_code = request.form.get("zip_code")
    status = request.form.get("status")
    status2 = request.form.get("status2")

    if password != confirm_password:
        return render_template("message.html", message="Password Not Matched")

    query = {"email": email}
    count = delivery_boy_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="Email Already Registered")

    query = {"phone": phone}
    count = delivery_boy_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="Number Already Registered")
    hashed_password = generate_password_hash(password)
    query = {"first_name": first_name,"last_name": last_name, "email": email, "phone": phone, "password": hashed_password,"dob":dob,"ssn":ssn, "address": address, "state": state, "city": city, "zip_code": zip_code, "status": 'unauthorized',"status2":'Available'}
    delivery_boy_collection.insert_one(query)
    return render_template("message.html", message="Delivery Boy Registration successful")

@app.route("/authorize_delivery_boy")
def authorize_delivery_boy():
    delivery_boy_id = request.args.get("delivery_boy_id")
    query = {"_id": ObjectId(delivery_boy_id)}
    query1 = {"$set":{"status": "authorized"}}
    delivery_boy_collection.update_one(query,query1)
    return redirect("/view_delivery_boys")

@app.route("/unauthorize_delivery_boy")
def unauthorize_delivery_boy():
    delivery_boy_id = request.args.get("delivery_boy_id")
    query = {"_id": ObjectId(delivery_boy_id)}
    query1 = {"$set": {"status": "unauthorized"}}
    delivery_boy_collection.update_one(query, query1)
    return redirect("/view_delivery_boys")

@app.route("/delivery_boy_home")
def delivery_boy_home():
    return render_template("delivery_boy_home.html")

@app.route("/view_delivery_boys")
def view_delivery_boys():
    query = {}
    delivery_boys = delivery_boy_collection.find(query)
    delivery_boys = list(delivery_boys)
    return render_template("view_delivery_boys.html",delivery_boys=delivery_boys)

@app.route("/db_profile")
def db_profile():
    delivery_boy_id = session['delivery_boy_id']
    query = {"_id":ObjectId(delivery_boy_id)}
    delivery_boy = delivery_boy_collection.find_one(query)
    return render_template("db_profile.html",delivery_boy=delivery_boy,delivery_boy_id=delivery_boy_id)

@app.route("/available")
def available():
    delivery_boy_id = request.args.get("delivery_boy_id")
    query = {'_id': ObjectId(delivery_boy_id)}
    query1 = {"$set":{"status2": "Available"}}
    delivery_boy_collection.update_one(query,query1)
    return redirect("/db_profile")

@app.route("/unavailable")
def unavailable():
    delivery_boy_id = request.args.get("delivery_boy_id")
    print(delivery_boy_id)
    query = {'_id': ObjectId(delivery_boy_id)}
    query1 = {"$set": {"status2": "Unavailable"}}
    delivery_boy_collection.update_one(query, query1)
    return redirect("/db_profile")

@app.route("/add_location")
def add_location():
    query = {}
    locations = locations_collection.find(query)
    locations = list(locations)
    message = request.args.get("message")
    return render_template("add_location.html",locations=locations,message=message)

@app.route("/add_location_action",methods=['post'])
def add_location_action():
    location_name = request.form.get("location_name")
    query = {"location_name": location_name}
    count = locations_collection.count_documents(query)
    if count > 0:
        return redirect("/add_location?message=Location Already Entered")
    else:
        locations_collection.insert_one(query)
        return redirect("/add_location?message=Location Entered Successfully")

@app.route("/edit_location")
def edit_location():
    location_id = request.args.get("location_id")
    location = locations_collection.find_one({'_id':ObjectId(location_id)})
    return render_template("edit_location.html",location=location)

@app.route("/edit_location_action", methods=["POST"])
def edit_location_action():
    location_id = request.form.get("location_id")
    location_name = request.form.get("location_name")
    query = {"$set": {"location_name": location_name}}
    locations_collection.update_one({'_id': ObjectId(location_id)}, query)
    return redirect("/add_location")

@app.route("/delete_location")
def delete_location():
    location_id = request.args.get("location_id")
    locations_collection.delete_one({"_id":ObjectId(location_id)})
    return redirect("/add_location")

@app.route("/add_food_categories")
def add_food_categories():
    query = {}
    food_categories = food_category_collection.find(query)
    message = request.args.get("message")
    return render_template("add_food_categories.html",food_categories=food_categories,message=message)

@app.route("/add_food_categories_action",methods=['post'])
def add_food_categories_action():
    food_category_name = request.form.get("food_category_name")
    query = {"food_category_name": food_category_name}
    count = food_category_collection.count_documents(query)
    if count > 0:
        return redirect("/add_food_categories?message=Food Category Already Entered")
    else:
        food_category_collection.insert_one(query)
        return redirect("/add_food_categories?message=Food Category Entered Successfully")
    
@app.route("/edit_food_categories")
def edit_food_categories():
    food_category_id = request.args.get("food_category_id")
    food_category = food_category_collection.find_one({'_id':ObjectId(food_category_id)})
    return render_template("edit_food_categories.html",food_category=food_category)

@app.route("/edit_food_categories_action", methods=["POST"])
def edit_food_categories_action():
    food_category_id = request.form.get("food_category_id")
    food_category_name = request.form.get("food_category_name")
    query = {"$set": {"food_category_name": food_category_name}}
    food_category_collection.update_one({'_id': ObjectId(food_category_id)}, query)
    return redirect("/add_food_categories")

@app.route("/delete_food_categories")
def delete_food_categories():
    food_category_id = request.args.get("food_category_id")
    food_category_collection.delete_one({"_id":ObjectId(food_category_id)})
    return redirect("/add_food_categories")
    
@app.route("/add_menu_items")
def add_menu_items():
    query = {}
    food_category = food_category_collection.find(query)
    food_categories = list(food_category)
    message = request.args.get("message")
    return render_template("add_menu_items.html",message=message,food_categories=food_categories,food_category=food_category)

@app.route("/add_menu_items_action",methods=['post'])
def add_menu_items_action():
    food_name = request.form.get("food_name")
    price = request.form.get("price")
    quantity = request.form.get("quantity")
    picture = request.files.get("picture")
    path = PICTURE_PATH+"/"+picture.filename
    picture.save(path)
    description = request.form.get("description")
    food_categories_id = request.form.get("food_categories_id")
    restaurant_id = session['restaurant_id']
    query = {"food_name": food_name}
    count = menu_items_collection.count_documents(query)
    if count > 0:
        return redirect("/add_menu_items?message=Already Food Item Exist")
    query = {"food_name": food_name, "price": price,"quantity":quantity, "picture": picture.filename, "description": description, "food_categories_id": ObjectId(food_categories_id), "restaurant_id": ObjectId(restaurant_id)}
    menu_items_collection.insert_one(query)
    return redirect("/add_menu_items?message=Food Item Added Successfully")

def get_restaurant_name_by_restaurant(restaurant_id):
    query = {"_id": restaurant_id}
    restaurant = restaurant_collection.find_one(query)
    return restaurant

def get_food_category_name_by_food_category(food_category_id):
    print(food_category_id)
    query = {"_id": ObjectId(food_category_id)}
    food_category = food_category_collection.find_one(query)
    return food_category

@app.route("/view_menu_items")
def view_menu_items():
    restaurant_id = request.args.get("restaurant_id")
    food_categories_id = request.args.get("food_categories_id")
    food_name = request.args.get("food_name")
    location_id = request.args.get("location_id")

    query = {}
    if session['role'] == "Restaurant":
        restaurant = session['restaurant_id']
        query = {"restaurant_id": ObjectId(restaurant)}
    elif session['role']=='Customer':
        if restaurant_id == None:
            restaurant_id = ""
        if food_categories_id == None:
            food_categories_id = ""
        if food_name == None:
            food_name = ""
        if location_id ==None:
            location_id=""
        query = {}
        if restaurant_id == "" and food_categories_id == "" and food_name == "" and location_id=='':
            query = {}
        if restaurant_id != "" and food_categories_id == "" and food_name == "" and location_id=='':
            query = {"restaurant_id": ObjectId(restaurant_id)}
        if restaurant_id == "" and food_categories_id != "" and food_name == "" and location_id=='':
            query = {"food_categories_id": ObjectId(food_categories_id)}
        if restaurant_id == "" and food_categories_id == "" and food_name != "" and location_id=="":
            query = {"food_name": food_name}
        if restaurant_id == "" and food_categories_id == "" and food_name == "" and location_id!='':
            restaurants = restaurant_collection.find({"location_id":ObjectId(location_id)})
            restaurant_ids = []
            for restaurant in restaurants:
                restaurant_ids.append({"restaurant_id":ObjectId(restaurant['_id'])})
            if len(restaurant_ids)==0:
                query = {"dd":''}
            else:
              query = {"$or":restaurant_ids}

    menu_items = menu_items_collection.find(query)
    menu_items = list(menu_items)
    query = {}
    restaurant = restaurant_collection.find(query)
    restaurants = list(restaurant)
    query = {}
    food_category = food_category_collection.find(query)
    food_categories = list(food_category)
    locations = locations_collection.find()
    locations = list(locations)
    return render_template("view_menu_items.html",menu_items=menu_items,locations=locations,get_restaurant_name_by_restaurant=get_restaurant_name_by_restaurant,get_food_category_name_by_food_category=get_food_category_name_by_food_category,food_categories=food_categories,restaurants=restaurants,str=str)

@app.route("/add_to_cart", methods=['post'])
def add_to_cart():
    quantity = request.form.get("quantity")
    menu_items_id = request.form.get("menu_item_id")
    menu_items = menu_items_collection.find_one({'_id':ObjectId(menu_items_id)})
    restaurant_id = menu_items['restaurant_id']
    customer_id = session['customer_id']
    query = {"customer_id": ObjectId(customer_id), "status": "Cart","restaurant_id":ObjectId(restaurant_id)}
    count = orders_collection.count_documents(query)
    if count == 0:
        result = orders_collection.insert_one({"customer_id": ObjectId(customer_id), "status": "Cart","date":datetime.datetime.now(),"restaurant_id":ObjectId(restaurant_id)})
        order_id = result.inserted_id
    else:
        orders = orders_collection.find_one(query)
        order_id = orders['_id']
    count = orders_collection.count_documents({"order_items.menu_items_id":ObjectId(menu_items_id),"order_items.order_id":ObjectId(order_id)})
    if count==0:
        order_items = {
            "menu_items_id":ObjectId(menu_items_id),
            "order_id":ObjectId(order_id),
            "quantity":quantity
        }
        orders_collection.update_one(
            {"_id":ObjectId(order_id)},
            {"$push": {"order_items": order_items}})
        return render_template("c_message.html", message="Item Added to Cart")
    else:
        orders = orders_collection.find_one(
            {
                "order_items.menu_items_id": ObjectId(menu_items_id)  # match document
            },
            {
                "order_items": {
                    "$elemMatch": {
                        "menu_items_id": ObjectId(menu_items_id)  # return only matching array item
                    }
                }
            }
        )
        for orders_item in orders['order_items']:
            print(orders_item)
            quantity1 = int(orders_item['quantity'])
            new_quantity = int(quantity1)+int(quantity)
            result = orders_collection.update_one(
                {
                    "order_items.menu_items_id": ObjectId(menu_items_id)  # find the right array item
                },
                {
                    "$set": {"order_items.$.quantity": new_quantity } # update just that item's quantity
                }
            )
        return render_template("c_message.html",message="Item Updated in Cart")

@app.route("/cart")
def cart():
    status = request.args.get("status")
    order_lenth=0
    query = {}
    if session['role'] == "Customer":
        order_lenth = orders_collection.find({'status': 'Cart', "customer_id": ObjectId(session['customer_id'])})
        order_lenth = list(order_lenth)
        order_lenth = (len(order_lenth))
        if status == "cart":
            query = {"status":'Cart', "customer_id": ObjectId(session['customer_id'])}
        elif status == "ordered":
            query = {"$or":[{"status":'Preparing'},{"status":'Ordered'},{"status":'Prepared'},{"status":'Dispatched'},{"status":'DeliveryBoy Assigned'}], "customer_id": ObjectId(session['customer_id'])}
        elif status=='history':
            query = {"$or":[{"status":'Delivered'},{"status":'Cancelled'}], "customer_id": ObjectId(session['customer_id'])}

    elif session['role'] == "Restaurant":
        if status == "ordered":
            query = {"$or":[{"status":'Preparing'},{"status":'Ordered'},{"status":'Prepared'}], "restaurant_id": ObjectId(session['restaurant_id'])}
        elif status=='dispatched':
            query = {"$or":[{"status":'Dispatched'},{"status":'DeliveryBoy Assigned'}], "restaurant_id": ObjectId(session['restaurant_id'])}
        elif status=='history':
            query = {"$or":[{"status":'Delivered'},{"status":'Cancelled'}], "restaurant_id": ObjectId(session['restaurant_id'])}
    elif session['role'] == "Delivery Boy":
        if status=='dispatched':
            query = {"$or":[{"status":'Dispatched'},{"status":'DeliveryBoy Assigned'}], "delivery_boy_id": ObjectId(session['delivery_boy_id'])}
        elif status=='history':
            query = {"$or":[{"status":'Delivered'},{"status":'Cancelled'}], "delivery_boy_id": ObjectId(session['delivery_boy_id'])}


    orders = orders_collection.find(query)
    orders = list(orders)
    delivery_boys = delivery_boy_collection.find()

    return render_template("cart.html",delivery_boys=delivery_boys,status=status,order_lenth=order_lenth,float=float,orders=orders,get_customer_name_by_customer=get_customer_name_by_customer,get_menu_item_price_by_menu_items_id=get_menu_item_price_by_menu_items_id,get_food_name_by_menu_items_id=get_food_name_by_menu_items_id,str=str,get_delivery_boy_name_by_delivery_boy=get_delivery_boy_name_by_delivery_boy)

@app.route("/add_quantity")
def add_quantity():
    order_id = request.args.get("order_id")
    menu_items_id = request.args.get("menu_items_id")
    orders = orders_collection.find_one(
        {
            "order_items.menu_items_id": ObjectId(menu_items_id)  # match document
        },
        {
            "order_items": {
                "$elemMatch": {
                    "menu_items_id": ObjectId(menu_items_id)  # return only matching array item
                }
            }
        }
    )
    print(orders)
    add_quantity = 0
    order_items = orders['order_items']
    for order_item in order_items:
        quantity = order_item['quantity']
        print(quantity)
        add_quantity = int(quantity)+1
    # menu_item = menu_items_collection.find_one({"_id":ObjectId(menu_items_id)})
    orders_collection.update_one(
        {
            "_id": ObjectId(order_id),
            "order_items.menu_items_id": ObjectId(menu_items_id)
        },
        {
            "$set": {"order_items.$.quantity": add_quantity}
        }
    )
    return redirect("/cart?status=cart")


@app.route("/remove_quantity")
def remove_quantity():
    order_id = request.args.get("order_id")
    menu_items_id = request.args.get("menu_items_id")
    orders = orders_collection.find_one(
        {
            "order_items.menu_items_id": ObjectId(menu_items_id)  # match document
        },
        {
            "order_items": {
                "$elemMatch": {
                    "menu_items_id": ObjectId(menu_items_id)  # return only matching array item
                }
            }
        }
    )
    print(orders)
    add_quantity = 0
    order_items = orders['order_items']
    for order_item in order_items:
        quantity = order_item['quantity']
        print(quantity)
        add_quantity = int(quantity) - 1
    # menu_item = menu_items_collection.find_one({"_id":ObjectId(menu_items_id)})
    orders_collection.update_one(
        {
            "_id": ObjectId(order_id),
            "order_items.menu_items_id": ObjectId(menu_items_id)
        },
        {
            "$set": {"order_items.$.quantity": add_quantity}
        }
    )
    return redirect("/cart?status=cart")



def get_customer_name_by_customer(customer_id):
    query = {"_id": ObjectId(customer_id)}
    customer = customer_collection.find_one(query)
    return customer

def get_delivery_boy_name_by_delivery_boy(delivery_boy_id):
    query = {"_id": ObjectId(delivery_boy_id)}
    delivery_boy = delivery_boy_collection.find_one(query)
    return delivery_boy

def get_menu_item_price_by_menu_items_id(menu_items_id):
    query = {"_id": ObjectId(menu_items_id)}
    menu_items = menu_items_collection.find_one(query)
    return menu_items

def get_food_name_by_menu_items_id(menu_items_id):
    query = {"_id": ObjectId(menu_items_id)}
    menu_items = menu_items_collection.find_one(query)
    return menu_items

@app.route("/order_now")
def order_now():
    order_id = request.args.get("order_id")
    total_price = request.args.get("total_price")
    return render_template("order_now.html",order_id=order_id,total_price=total_price)

@app.route("/order_now2")
def order_now2():
    customer_id = session['customer_id']
    orders = orders_collection.find({"status":'Cart',"customer_id":ObjectId(customer_id)})
    total_price = 0
    for order in orders:
        for order_item in order['order_items']:
            menu_items_id = order_item['menu_items_id']
            menu_items = menu_items_collection.find_one({"_id":ObjectId(menu_items_id)})
            total_price = float(total_price)+float(menu_items['price'])*float(order_item['quantity'])
    return render_template("order_now2.html",total_price=total_price)

@app.route("/order_now_action",methods=['post'])
def order_now_action():
    order_id = request.form.get("order_id")
    total_price = request.form.get("total_price")
    order_type = request.form.get("order_type")
    date = datetime.datetime.now()
    card_type = request.form.get("card_type")
    card_number = request.form.get("card_number")
    holder_name = request.form.get("holder_name")
    cvv = request.form.get("cvv")
    expiry_date = request.form.get("expiry_date")
    query = {"$set" : {"status": "Ordered", "total_price": total_price,"order_type":order_type}}
    orders_collection.update_one({"_id":ObjectId(order_id)},query)
    payments_collection.insert_one({"date":date,"order_id":ObjectId(order_id),"status":'Paid',"card_type": card_type,"card_number": card_number,"holder_name": holder_name,"cvv": cvv,"expiry_date": expiry_date,"order_type":order_type,"total_price":total_price})
    return render_template("c_message.html",message="Order Placed Successfully")




@app.route("/order_now_action2",methods=['post'])
def order_now_action2():
    total_price = request.form.get("total_price")
    order_type = request.form.get("order_type")
    date = datetime.datetime.now()
    card_type = request.form.get("card_type")
    card_number = request.form.get("card_number")
    holder_name = request.form.get("holder_name")
    cvv = request.form.get("cvv")
    expiry_date = request.form.get("expiry_date")
    orders = orders_collection.find({"status":'Cart',"customer_id":ObjectId(session['customer_id'])})
    for order in orders:
        total_price2=0
        for order_item in order['order_items']:
            menu_items_id = order_item['menu_items_id']
            menu_items = menu_items_collection.find_one({"_id": ObjectId(menu_items_id)})
            total_price2 = total_price2+float(menu_items['price']) * float(order_item['quantity'])
        query = {"$set" : {"status": "Ordered", "total_price": total_price2,"order_type":order_type}}
        orders_collection.update_one({"_id":ObjectId(order['_id'])},query)
        payments_collection.insert_one({"date":date,"order_id":ObjectId(order['_id']),"status":'Paid',"card_type": card_type,"card_number": card_number,"holder_name": holder_name,"cvv": cvv,"expiry_date": expiry_date,"order_type":order_type,"total_price":total_price})
    return render_template("c_message.html",message="Order Placed Successfully")

@app.route("/update_order_status")
def update_order_status():
    order_id = request.args.get("order_id")
    message = request.args.get("message")
    status = request.args.get("status")
    query = {"$set": {"status":status}}
    orders_collection.update_one({"_id":ObjectId(order_id)},query)
    return render_template("r_message.html",message=message)

@app.route("/assign_delivery_boy")
def assign_delivery_boy():
    order_id = request.args.get("order_id")
    # query = {"status2":'Available'}
    delivery_boy = delivery_boy_collection.find()
    delivery_boys = list(delivery_boy)
    return render_template("assign_delivery_boy.html",order_id=order_id,delivery_boys=delivery_boys)

@app.route("/assign_now")
def assign_now():
    delivery_boy_id = request.args.get("delivery_boy_id")
    delivery_boy = delivery_boy_collection.find_one({"_id":ObjectId(delivery_boy_id)})
    if delivery_boy['status2']=='Unavailable':
        return render_template("r_message.html", message="Delivery boy not available can not Assigned To Delivery Boy")
    order_id = request.args.get("order_id")
    query = {"$set":{"status":'DeliveryBoy Assigned',"delivery_boy_id":ObjectId(delivery_boy_id)}}
    orders_collection.update_one({"_id":ObjectId(order_id)},query)
    return render_template("c_message.html",message="Assigned To Delivery Boy")

@app.route("/assign_now_update")
def assign_now_update():
    order_id = request.args.get("order_id")
    query = {"$set":{"status":'Dispatched'}}
    orders_collection.update_one({"_id":ObjectId(order_id)},query)
    return render_template("db_message.html",message="Order Dispatched")

@app.route("/dispatched_update")
def dispatched_update():
    order_id = request.args.get("order_id")
    query = {"$set":{"status":'Delivered'}}
    orders_collection.update_one({"_id":ObjectId(order_id)},query)
    return render_template("c_message.html",message="Order Delivered")

@app.route("/view_payment")
def view_payment():
    order_id = request.args.get("order_id")
    total_price = request.form.get("total_price")
    payment = payments_collection.find_one({"order_id": ObjectId(order_id)})
    return render_template("view_payment.html", payment=payment,total_price=total_price,order_id=order_id,get_order_by_order_id=get_order_by_order_id,get_customer_name_by_customer=get_customer_name_by_customer)

def get_order_by_order_id(order_id):
    query = {"_id": ObjectId(order_id)}
    order = orders_collection.find_one(query)
    return order

@app.route("/cancel_order")
def cancel_order():
    order_id = request.args.get("order_id")
    query = {"_id": ObjectId(order_id)}
    query1 = {"$set":{"status":"Cancelled"}}
    orders_collection.update_one(query,query1)
    return render_template("c_message.html",message="Your Order Cancelled")


@app.route("/remove_cart")
def remove_cart():
    order_id = request.args.get("order_id")
    menu_items_id = request.args.get("menu_items_id")
    result = orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$pull": {"order_items": {"menu_items_id": ObjectId(menu_items_id)}}}
    )
    order = orders_collection.find_one({"_id":ObjectId(order_id)})
    print(len(order['order_items']))
    if len(order['order_items'])==0:
        orders_collection.delete_one({"_id":ObjectId(order_id)})
    return redirect("/view_menu_items")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(debug=True)



