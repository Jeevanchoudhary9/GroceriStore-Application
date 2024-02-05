import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from app import app
from functools import wraps
from models import db, User, Profile, Product, Category, Cart, Order
import random
import razorpay


def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner

def manager_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        if User.query.filter_by(userid=session['user_id']).first().role!="manager":
            flash('You are not authorized to access this page')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner



@app.route('/')
@auth_required
def index():
    return render_template('index.html',user=User.query.filter_by(userid=session['user_id']).first(),nav="dashboard",categories=Category.query.all(),products=Product.query.all())

@app.route('/profile')
@auth_required
def profile():
    profile=(User.query.filter_by(userid=session['user_id']).first()).profileid
    return render_template('profile.html',profile=Profile.query.filter_by(profileid=profile).first(),user=User.query.filter_by(userid=session['user_id']).first(),nav="profile")

@app.route('/profile',methods=["POST"])
@auth_required
def profile_post():
    user=User.query.filter_by(userid=session['user_id']).first()
    address=request.form.get('address')
    cpassword=request.form.get('cpassword')
    npassword=request.form.get('npassword')
    profile=Profile.query.filter_by(profileid=user.profileid).first()

    if address is None :
        flash('Please fill the required fields')
        return redirect(url_for('profile'))
    elif address!='' and cpassword=='' and npassword=='':
        profile.address=address
        db.session.commit()
    elif address!='' or cpassword!='' or npassword!='':
        if not user.check_password(cpassword):
            flash('Please check your password and try again.')
            return redirect(url_for('profile'))
        if npassword == cpassword:
            flash('New password cannot be same as old password')
            return redirect(url_for('profile'))
        else:
            user.password=npassword
            profile.address=address
            db.session.commit()
    flash(['Profile updated successfully','success'])
    return redirect(url_for('profile'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=["POST"])
def login_post():
    username=request.form.get('username')
    password=request.form.get('password')

    if username=='' or password=='':
        flash('Please fill the required fields')
        return redirect(url_for('login'))
    
    user=User.query.filter_by(uname=username).first()
    if not user:
        flash('Please check your username and try again.')
        return redirect(url_for('login'))
    if not user.check_password(password):
        flash('Please check your password and try again.')
        return redirect(url_for('login'))
    #after successful login   
    session['user_id']=user.userid
    return redirect(url_for('index'))

@app.route('/login_man')
def login_man():
    return render_template('login_man.html')

@app.route('/login_man', methods=["POST"])
def login_man_post():
    username=request.form.get('username')
    password=request.form.get('password')

    if username is None or password is None:
        flash('Please fill the required fields')
        return redirect(url_for('login_man'))
    
    user=User.query.filter_by(uname=username).first()
    
    if not user or User.query.filter_by(uname=username).first().role!="manager":
        flash('Please check your username and try again or go to customer login.')
        return redirect(url_for('login_man'))
    if not user.check_password(password):
        flash('Please check your password and try again.')
        return redirect(url_for('login_man'))
    if user and User.query.filter_by(uname=username).first().role=="manager":
        #after successful login   
        session['user_id']=user.userid
        return redirect(url_for('manager_index'))
    
    return redirect(url_for('login_man'))

@app.route('/manager_index')
@auth_required
@manager_required
def manager_index():
    user=User.query.filter_by(userid=session['user_id']).first()
    products = Product.query.all()
    return render_template('manager_index.html',user=user,nav="dashboard",categories=Category.query.all(),products=products)

@app.route('/category/add')
@auth_required
@manager_required
def add_category():
    
    return render_template('category/add_category.html',nav="add_category")

@app.route('/category/add',methods=["POST"])
@auth_required
@manager_required
def add_category_post():
    
    
    categoryname=request.form.get('categoryname')
    if categoryname is None:
        flash('Please fill the required fields')
        return redirect(url_for('add_category'))
    if len(categoryname)>50:
        flash('Category name cannot be more than 50 characters')
        return redirect(url_for('add_category'))
    if Category.query.filter_by(categoryname=categoryname).first()!=None:
        flash('Category name already exists')
        return redirect(url_for('add_category'))
    
    category=Category(categoryname=categoryname)
    db.session.add(category)
    db.session.commit()
    flash(['Category added successfully','success'])
    return redirect(url_for('manager_index'))

@app.route('/category/<int:categoryid>/edit')
@auth_required
@manager_required
def edit_category(categoryid):
    return render_template('category/edit_category.html',category=Category.query.filter_by(categoryid=categoryid).first(),nav="edit_category")

@app.route('/category/<int:categoryid>/edit',methods=["POST"])
@auth_required
@manager_required
def edit_category_post(categoryid):

    categoryname=request.form.get('categoryname')
    if categoryname is None:
        flash('Please fill the required fields')
        return redirect(url_for('edit_category',categoryid))
    if len(categoryname)>50:
        flash('Category name cannot be more than 50 characters')
        return redirect(url_for('edit_category',categoryid))
    if Category.query.filter_by(categoryname=categoryname).first()!=None:
        flash('Category name already exists')
        return redirect(url_for('edit_category',categoryid))
    
    category=Category.query.filter_by(categoryid=categoryid).first()
    category.categoryname=categoryname
    db.session.commit()
    flash(['Category edited successfully','success'])
    return redirect(url_for('manager_index'))


@app.route('/category/<int:categoryid>/delete')
@auth_required
@manager_required
def delete_category(categoryid):
    
    return render_template('category/delete_category.html',category=Category.query.filter_by(categoryid=categoryid).first(),nav="delete_category")

@app.route('/category/<int:categoryid>/delete',methods=["POST"])
@auth_required
@manager_required
def delete_category_post(categoryid):

    category=Category.query.filter_by(categoryid=categoryid).first()
    products=Product.query.filter_by(categoryid=categoryid).all()
    
    for product in products:
        carts=Cart.query.filter_by(productid=product.productid).all()
        db.session.delete(product)
        
        for cart in carts:
            db.session.delete(cart)

    db.session.delete(category)
    db.session.commit()
    flash(['Category deleted successfully','success'])
    return redirect(url_for('manager_index'))


@app.route('/product/<int:categoryid>/add')
@auth_required
@manager_required
def add_product(categoryid):
    return render_template('product/add_product.html',categories=Category.query.filter_by(categoryid=categoryid).first(),nav="add_product")

@app.route('/product/<int:categoryid>/add',methods=["POST"])
@auth_required
@manager_required
def add_product_post(categoryid):
    
    productname=request.form.get('productname')
    categoryid=Category.query.filter_by(categoryid=categoryid).first().categoryid
    
    productunit=request.form.get('productunit')
    rateperunit=request.form.get('rateperunit')
    quantity=request.form.get('productquantity')

    if productname is None or categoryid is None or rateperunit is None or productunit is None or quantity is None:
        flash('Please fill the required fields')
        return redirect(url_for('add_product',categoryid=categoryid))
    if len(productname)>50:
        flash('Product name cannot be more than 50 characters')
        return redirect(url_for('add_product',categoryid=categoryid))
    if Product.query.filter_by(productname=productname).first()!=None:
        flash('Product name already exists')
        return redirect(url_for('add_product',categoryid=categoryid))
    if not rateperunit.isdigit():
        flash('Rate per unit should be a number')
        return redirect(url_for('add_product',categoryid=categoryid))
    if not quantity.isdigit():
        flash('Quantity should be a number')
        return redirect(url_for('add_product',categoryid=categoryid))
    
    
    
    product=Product(productname=productname,categoryid=categoryid,rateperunit=rateperunit,unit=productunit,quantity=quantity)
    db.session.add(product)
    db.session.commit()
    flash(['Product added successfully','success'])
    return redirect(url_for('manager_index'))


@app.route('/product/<int:productid>/edit')
@auth_required
@manager_required
def edit_product(productid):
    return render_template('product/edit_product.html',product=Product.query.filter_by(productid=productid).first(),nav="edit_product")

@app.route('/product/<int:productid>/edit',methods=["POST"])
@auth_required
@manager_required
def edit_product_post(productid):
    
    productname=request.form.get('productname')#banana
    productrateperunit=request.form.get('rateperunit')#25.0
    productunit=request.form.get('productunit')#rs/kg
    productquantity=request.form.get('productquantity')#75

    if productname is None or productrateperunit is None or productunit is None or productquantity is None:
        flash('Please fill the required fields')
        return redirect(url_for('edit_product',productid=productid))
    if len(productname)>20:
        flash('Product name cannot be more than 20 characters')
        return redirect(url_for('edit_product',productid=productid))
    try:
        productrateperunit=float(productrateperunit)
    except:
        flash('Rate per unit should be a number')
        return redirect(url_for('edit_product',productid=productid))
    if not productquantity.isdigit():
        flash('Quantity should be a number')
        return redirect(url_for('edit_product',productid=productid))
    
    
    product=Product.query.filter_by(productid=productid).first()

    product.productname=productname
    product.rateperunit=productrateperunit
    product.unit=productunit
    product.quantity=productquantity
    

    

    db.session.commit()
    flash(['Product edited successfully','success'])
    return redirect(url_for('manager_index'))


@app.route('/product/<int:productid>/delete')
@auth_required
@manager_required
def delete_product(productid):
    
    return render_template('product/delete_product.html',product=Product.query.filter_by(productid=productid).first(),nav="delete_product")

@app.route('/product/<int:productid>/delete',methods=["POST"])
@auth_required
@manager_required
def delete_product_post(productid):
    product=Product.query.filter_by(productid=productid).first()
    carts=Cart.query.filter_by(productid=productid).all()
    for cart in carts:
        db.session.delete(cart)
    db.session.delete(product)
    db.session.commit()
    flash(['Product deleted successfully','success'])
    return redirect(url_for('manager_index'))


@app.route('/product/<int:productid>/buy')
@auth_required
def buy_product(productid):
    return render_template('cart/buy_product.html',product=Product.query.filter_by(productid=productid).first(),nav="buy_product",category=Category.query.filter_by(categoryid=Product.query.filter_by(productid=productid).first().categoryid).first())

@app.route('/product/<int:productid>/buy',methods=["POST"])
@auth_required
def buy_product_post(productid):

    cart = Cart.query.filter_by(userid=session['user_id']).all() 
    cartid=random.randint(1,100000)
    
    product=Product.query.filter_by(productid=productid).first()
    quantity=request.form.get('quantity')
    if quantity is None:
        flash('Please fill the required fields')
        return redirect(url_for('buy_product',productid=productid))
    if not quantity.isdigit():
        flash('Quantity should be a number')
        return redirect(url_for('buy_product',productid=productid))
    if int(quantity)>product.quantity:
        flash('Quantity should be less than or equal to available quantity')
        return redirect(url_for('buy_product',productid=productid))
    
    client=razorpay.Client(auth=("rzp_test_egexvRe956lDwz","YTeaupG98A30jK23UlUzjYVY"))
    payment=client.order.create({'amount':int((product.rateperunit * int(quantity))*100),'currency':'INR','payment_capture':'1'})
    name=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().firstname+" "+Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().lastname
    email=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().email
    phone=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().phone

    return render_template('buy_payment.html',productid=productid,email=email,phone=phone,name=name,payment=payment,productname=product.productname,categoryname=Category.query.filter_by(categoryid=product.categoryid).first().categoryname,quantity=quantity,rateperunit=product.rateperunit,unit=product.unit,amount=(product.rateperunit * int(quantity)),nav="payment",user=User.query.filter_by(userid=session['user_id']).first())
    

@app.route('/buy_payment/<int:productid>/<int:quantity>',methods=["POST"])
@auth_required
def buy_payment(productid,quantity):
    cart = Cart.query.filter_by(userid=session['user_id']).all() 
    cartid=random.randint(1,100000)
    
    product=Product.query.filter_by(productid=productid).first()
    
    order=Order(userid=session['user_id'],productid=product.productid,quantity=quantity,dateoftransaction=datetime.datetime.now(),cartid=cartid,productname=product.productname,categoryname=Category.query.filter_by(categoryid=product.categoryid).first().categoryname,rateperunit=product.rateperunit,unit=product.unit,amount=(product.rateperunit * int(quantity)),categoryid=product.categoryid)
    
    
    db.session.add(order)
    product.quantity=product.quantity-int(quantity)
    db.session.add(product)
    db.session.commit()
    flash(['Thank you for Shopping','success'])
    return redirect(url_for('index'))


@app.route('/cart')
@auth_required
def cart():
    cart = Cart.query.filter_by(userid=session['user_id']).all()
    products = []
    grand_total=[]
    total_amount=0
    for item in cart:
        product_details = Product.query.filter_by(productid=item.productid).first()
        category_details = Category.query.filter_by(categoryid=product_details.categoryid).first()
        cart=Cart.query.filter_by(userid=session['user_id'],productid=item.productid).all()
        total_amount=total_amount+(Cart.query.filter_by(userid=session['user_id'],productid=item.productid).first().quantity*product_details.rateperunit)
        

        products.append({
            'productid': product_details.productid,
            'productname': product_details.productname,
            'categoryname': category_details.categoryname,
            'rateperunit': product_details.rateperunit,
            'unit': product_details.unit,
            'quantity': int(item.quantity),
            'amount': product_details.rateperunit * item.quantity,
            'stock': int(product_details.quantity),
            
        })
    grand_total.append({'grand_total':total_amount})
    return render_template('cart/cart.html', products=products,grand_total=grand_total,nav="cart",user=User.query.filter_by(userid=session['user_id']).first())

@app.route('/cart',methods=["POST"])
@auth_required
def cart_post():
    return ""

@app.route('/cart/<int:productid>/review_product')
@auth_required
def review_product(productid):
    return render_template('cart/review_product.html',product=Product.query.filter_by(productid=productid).first(),nav="review_product",category=Category.query.filter_by(categoryid=Product.query.filter_by(productid=productid).first().categoryid).first(),cart=Cart.query.filter_by(userid=session['user_id'],productid=productid).first())

@app.route('/cart/<int:productid>/review_product',methods=["POST"])
@auth_required
def review_product_post(productid):
    product=Product.query.filter_by(productid=productid).first()
    quantity=request.form.get('quantity')
    quantity = int(quantity)
    cart=Cart.query.filter_by(userid=session['user_id'],productid=productid).first()

    if quantity is None:
        flash('Please fill the required fields')
        return redirect(url_for('review_product',productid=productid))
    elif quantity<=0:
        flash('Quantity should be greater than 0')
        return redirect(url_for('review_product',productid=productid))
    elif int(quantity)>product.quantity:
        flash('Quantity should be less than or equal to available quantity')
        return redirect(url_for('review_product',productid=productid))
    elif product.quantity==0:
        flash('Product is out of stock')
        return redirect(url_for('review_product',productid=productid))
    elif product.quantity<int(quantity):
        flash('Product quantity is less than required quantity')
        return redirect(url_for('review_product',productid=productid))
    
        
    else:
        cart.quantity=quantity
        db.session.commit()
        flash(['Reviewed Cart','success'])
        return redirect(url_for('cart'))
    

    
@app.route('/cart/<int:productid>/delete_product')
@auth_required
def delete_product_cart(productid):
    cart=Cart.query.filter_by(userid=session['user_id'],productid=productid).first()
    db.session.delete(cart)
    db.session.commit()
    flash(['Product Removed from cart','success'])
    return redirect(url_for('cart'))


@app.route('/product/<int:productid>/addtocart')
@auth_required
def addtocart(productid):
    return render_template('cart/buy_product.html',product=Product.query.filter_by(productid=productid).first(),nav="addtocart",category=Category.query.filter_by(categoryid=Product.query.filter_by(productid=productid).first().categoryid).first())

@app.route('/product/<int:productid>/addtocart',methods=["POST"])
@auth_required
def addtocart_post(productid):
    product=Product.query.filter_by(productid=productid).first()
    quantity=request.form.get('quantity')
    cart=Cart(userid=session['user_id'],productid=productid,quantity=quantity)

    
    if quantity is None:
        flash('Please fill the required fields')
        return redirect(url_for('addtocart',productid=productid))
    if not quantity.isdigit():
        flash('Quantity should be a number')
        return redirect(url_for('addtocart',productid=productid))
    if int(quantity)>product.quantity:
        flash('Quantity should be less than or equal to available quantity')
        return redirect(url_for('addtocart',productid=productid))
    if product.quantity==0:
        flash('Product is out of stock')
        return redirect(url_for('addtocart',productid=productid))
    if product.quantity<int(quantity):
        flash('Product quantity is less than required quantity')
        return redirect(url_for('addtocart',productid=productid))
    
    if Cart.query.filter_by(userid=session['user_id'],productid=productid).first()!=None:
        cart=Cart.query.filter_by(userid=session['user_id'],productid=productid).first()
        cart.quantity=cart.quantity+int(quantity)
        db.session.commit()
        flash(['Product added to cart successfully','success'])

        return redirect(url_for('addtocart',productid=productid))
    
    
    db.session.add(cart)
    db.session.commit()
    flash(['Product added to cart successfully','success'])
    return redirect(url_for('index'))

@app.route('/cart/buy_all')
@auth_required
def buy_all():
    cart = Cart.query.filter_by(userid=session['user_id']).all() 

    cartid=random.randint(1,100000)

    for item in cart:
        product_details = Product.query.filter_by(productid=item.productid).first()
        if product_details.quantity==0:
            continue
        elif product_details.quantity<item.quantity:
            continue
        else:
            order=Order(userid=session['user_id'],productid=item.productid,quantity=item.quantity,dateoftransaction=datetime.datetime.now(),cartid=cartid,productname=product_details.productname,categoryname=Category.query.filter_by(categoryid=product_details.categoryid).first().categoryname,rateperunit=product_details.rateperunit,unit=product_details.unit,amount=(product_details.rateperunit * item.quantity),categoryid=product_details.categoryid)
            product_details.quantity = product_details.quantity - item.quantity
            db.session.add(order)
            db.session.add(product_details)
            db.session.delete(item)
            db.session.commit()

    flash(['Thank you for Shopping','success'])
    return redirect(url_for('index'))

@app.route('/order')
@auth_required
def order():
    orders = Order.query.filter_by(userid=session['user_id']).all()
    distinct_carts = Order.query.with_entities(Order.cartid).filter_by(userid=session['user_id']).distinct().all()
    cart_ids = [row[0] for row in distinct_carts]

    orders = []
    orders1=[]

    grand=0
    for item in cart_ids:
        for order in Order.query.filter_by(cartid=item).all():
            product_details = Product.query.filter_by(productid=order.productid).first()
            grand=grand+order.rateperunit * order.quantity
            orders.append({
                'productid': order.productid,
                'productname': order.productname,
                'categoryname': order.categoryname,
                'rateperunit': order.rateperunit,
                'unit': order.unit,
                'quantity': order.quantity,
                'amount': order.rateperunit * order.quantity,
                'dateoftransaction':order.dateoftransaction,
                'cartid':order.cartid,
                'grand':grand
            })
        orders1.append(orders)
        grand=0
        orders=[]
        
        
    
    return render_template('order.html', orders=orders1, nav="order", user=User.query.filter_by(userid=session['user_id']).first())





    

@app.route('/register',methods=["GET"])
def register():
    return render_template('register.html')

@app.route('/register',methods=["POST"])
def register_post():
    username=request.form.get('username')
    password=request.form.get('password')
    firstname=request.form.get('firstname')
    lastname=request.form.get('lastname')
    email=request.form.get('email')
    phone=request.form.get('phone')
    address=request.form.get('address')

    if username is None or password is None or email is None :
        flash('Please fill the required fields')
        return redirect(url_for('register'))
    
    if User.query.filter_by(uname=username).first():
        flash('Username already exists')
        return redirect(url_for('register'))
    
    def user(username, password, role="customer",Profileid=None):
        return User(uname=username,password=password,profileid=Profileid,role=role)
    
    profile=Profile(firstname=firstname,lastname=lastname,email=email,phone=phone,address=address)
    db.session.add(profile)
    db.session.commit()
    pid=Profile.query.filter_by(firstname=firstname,lastname=lastname,email=email,phone=phone,address=address).first().profileid
    user=user(username,password,Profileid=pid)
    db.session.add(user)
    db.session.commit()
    flash(['You have successfully registered','success'])
    
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('login'))


def extract_month():
    results = Order.query.all()
    months = {
        "Jan": [0,0], "Feb": [0,0], "Mar": [0,0], "Apr": [0,0], "May": [0,0], "Jun": [0,0],
        "Jul": [0,0], "Aug": [0,0], "Sep": [0,0], "Oct": [0,0], "Nov": [0,0], "Dec": [0,0]
    }
    categoryDict={}
    productDict={}

    for result in results:
        entity=categoryDict.get(result.categoryname,[0,0])
        categoryDict[result.categoryname]=[entity[0]+result.quantity,entity[1]+result.amount]
    
    for result in results:
        entity=productDict.get(result.productname,[0,0])
        productDict[result.productname]=[entity[0]+result.quantity,entity[1]+result.amount]

    for result in results:
        month = result.dateoftransaction.strftime('%b')
        months[month][0] += 1 # Number of orders
        months[month][1] += result.amount # Total amount
    

    return months,categoryDict,productDict

@app.route('/summary')
@auth_required
@manager_required
def summary():
    months = extract_month()[0]
    categoryDict=extract_month()[1]
    productDict=extract_month()[2]
    
    return render_template('summary.html', months=months,categoryDict=categoryDict,productDict=productDict, nav="summary")


# payment
@app.route('/payment')
@auth_required 
def payment():
    
    
    cart = Cart.query.filter_by(userid=session['user_id']).all()
    products = []
    grand_total=[]
    total_amount=0

    username=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().firstname+" "+Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().lastname
    email=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().email
    phone=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().phone
    
    for item in cart:
        
        product_details = Product.query.filter_by(productid=item.productid).first()

        if product_details.quantity==0:
            flash('Product is out of stock')
            continue
        elif product_details.quantity<item.quantity:
            flash('Product quantity is less than required quantity')
            continue
        else:
            category_details = Category.query.filter_by(categoryid=product_details.categoryid).first()
            cart=Cart.query.filter_by(userid=session['user_id'],productid=item.productid).all()
            total_amount=total_amount+(Cart.query.filter_by(userid=session['user_id'],productid=item.productid).first().quantity*product_details.rateperunit)
            
            products.append({
                'productid': product_details.productid,
                'productname': product_details.productname,
                'categoryname': category_details.categoryname,
                'rateperunit': product_details.rateperunit,
                'unit': product_details.unit,
                'quantity': int(item.quantity),
                'amount': product_details.rateperunit * item.quantity,
                'stock': int(product_details.quantity),
                
            })
    grand_total.append({'grand_total':total_amount})
    total_amount_after=total_amount

    if total_amount>500000:
        flash('Maximum amount for payment is 500000')
        return redirect(url_for('cart'))
    if total_amount>40000:
        total_amount_after=40000
    client=razorpay.Client(auth=("rzp_test_egexvRe956lDwz","YTeaupG98A30jK23UlUzjYVY"))
    payment=client.order.create({'amount':int(total_amount_after*100),'currency':'INR','payment_capture':'1'})


    return render_template('payment.html',username=username,email=email,phone=phone,payment=payment,products=products,grand_total=grand_total,nav="payment",user=User.query.filter_by(userid=session['user_id']).first())


@app.route('/success',methods=["post"])
@auth_required
def success():
    
    cart = Cart.query.filter_by(userid=session['user_id']).all()
    products = []
    grand_total=[]
    total_amount=0

    username=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().firstname+" "+Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().lastname
    email=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().email
    phone=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().phone
    
    for item in cart:
        
        product_details = Product.query.filter_by(productid=item.productid).first()

        if product_details.quantity==0:
            continue
        elif product_details.quantity<item.quantity:
            continue
        else:
            category_details = Category.query.filter_by(categoryid=product_details.categoryid).first()
            cart=Cart.query.filter_by(userid=session['user_id'],productid=item.productid).all()
            total_amount=total_amount+(Cart.query.filter_by(userid=session['user_id'],productid=item.productid).first().quantity*product_details.rateperunit)
            
            products.append({
                'productid': product_details.productid,
                'productname': product_details.productname,
                'categoryname': category_details.categoryname,
                'rateperunit': product_details.rateperunit,
                'unit': product_details.unit,
                'quantity': int(item.quantity),
                'amount': product_details.rateperunit * item.quantity,
                'stock': int(product_details.quantity),
                
            })
    grand_total.append({'grand_total':total_amount})
    message="Thank You for Shopping from Groceri Store"
    buy_all()
    return render_template('success.html',message=message,username=username,email=email,phone=phone,payment=payment,products=products,grand_total=grand_total,nav="success",user=User.query.filter_by(userid=session['user_id']).first())


@app.route('/order_success/<int:cartid>')
@auth_required
def order_success(cartid):
    orders = []
    grand=0
    username=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().firstname+" "+Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().lastname
    email=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().email
    phone=Profile.query.filter_by(profileid=(User.query.filter_by(userid=session['user_id']).first().profileid)).first().phone

    for order in Order.query.filter_by(cartid=cartid).all():
            product_details = Product.query.filter_by(productid=order.productid).first()
            grand=grand+order.rateperunit * order.quantity
            orders.append({
                'productid': order.productid,
                'productname': order.productname,
                'categoryname': order.categoryname,
                'rateperunit': order.rateperunit,
                'unit': order.unit,
                'quantity': order.quantity,
                'amount': order.rateperunit * order.quantity,
                'dateoftransaction':order.dateoftransaction,
                'cartid':order.cartid,
                'grand':grand
            })
    print(orders)
    return render_template('order_success.html',username=username,email=email,phone=phone, cartid=cartid,orders=orders, grand=grand, nav="success", user=User.query.filter_by(userid=session['user_id']).first())
