from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db=SQLAlchemy(app)

class User(db.Model):
    __TableName__ = 'user'
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    uname = db.Column(db.String(20), nullable=False, unique=True)
    passhash = db.Column(db.String(1024), nullable=False)
    profileid = db.Column(db.String(1024), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)
     
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Profile(db.Model):
    __TableName__ = 'profile'
    profileid = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20))
    email = db.Column(db.String(50), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(100))
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)

"""class Session(db.Model):
    __TableName__ = 'session'
    sessionid = db.Column(db.String(20), primary_key=True, nullable=False, unique=True, autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=False, unique=True)
    sessiontime = db.Column(db.DateTime, nullable=False,default=timedelta(minutes=30))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)"""

class Product(db.Model):
    __TableName__ = 'product'
    productid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    productname = db.Column(db.String(20), nullable=False)
    categoryid = db.Column(db.Integer, db.ForeignKey('category.categoryid'), nullable=False)
    rateperunit = db.Column(db.Float, nullable=False)
    unit= db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    #manufacturer_date = db.Column(db.DateTime, nullable=False)
    #description = db.Column(db.String(100))
    #image = db.Column(db.String(100))
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)

    #relationship
    # discounts = db.relationship('Discount', back_populates='product')

class Category(db.Model):
    __TableName__ = 'category'
    categoryid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    # productid = db.Column(db.Integer, db.ForeignKey('product.productid'), nullable=False)
    categoryname = db.Column(db.String(50), nullable=False)
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)
    #relationship
    products = db.relationship('Product', backref='category', foreign_keys='Product.categoryid', lazy=True)
    
class Cart(db.Model):
    __TableName__ = 'cart'
    cartid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    productid = db.Column(db.Integer, db.ForeignKey('product.productid'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)

"""class Discount(db.Model):
    __TableName__ = 'discount'
    discountid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    discountdetails = db.Column(db.String(20), nullable=False)
    productid = db.Column(db.Integer, db.ForeignKey('product.productid'), nullable=False)
    discountpercent = db.Column(db.Float, nullable=False)
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)   
    product = db.relationship('Product', backref='discount_links')"""

class Order(db.Model):
    __TableName__ = 'order'
    orderid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    productid = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    dateoftransaction = db.Column(db.DateTime, nullable=False)
    cartid = db.Column(db.Integer, nullable=False)
    productname = db.Column(db.String(20), nullable=False)
    categoryname = db.Column(db.String(50), nullable=False)
    rateperunit = db.Column(db.Float, nullable=False)
    unit= db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    categoryid = db.Column(db.Integer, nullable=False)
    delivery_status = db.Column(db.Integer, nullable=False, default=0)
    #sessionid = db.Column(db.String(20), db.ForeignKey('session.sid'), nullable=True)

with app.app_context():
    db.create_all()

    admin=User.query.filter_by(uname='admin').first()
    if not admin:
        admin=User(uname='admin', password='admin', role='manager', profileid='1')
        admin_profile=Profile(profileid='1', firstname='admin', lastname='admin',email='admin',phone='admin',address='admin')
        db.session.add(admin)
        db.session.add(admin_profile)
        db.session.commit()