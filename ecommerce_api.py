from flask import Flask, jsonify, request 
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, registry
from sqlalchemy import select, ForeignKey, delete, Column, String, Integer, Table, Float, Date, MetaData
from flask_marshmallow import Marshmallow 
from sqlalchemy.ext.declarative import declarative_base
from marshmallow import fields, validate, ValidationError
from typing import List
from datetime import datetime, date



app = Flask(__name__)
cors = CORS(app) 
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:Chima1964!@localhost/e_commerce_db2"
app.json.sort_keys = False 
db = SQLAlchemy(app)
ma = Marshmallow(app)
registry = registry()
metadata = MetaData
Base = declarative_base(cls = db.Model)
app.app_context().push()

class Customer(Base):
    
    __tablename__ = "Customers"
    
    customer_id: Mapped[int] = mapped_column(autoincrement=True, primary_key = True)
    name: Mapped[str] = mapped_column(db.String(255)) #VARCHAR(255) in sql
    email: Mapped[str] = mapped_column(db.String(320))
    phone: Mapped[str] = mapped_column(db.String(15))
    
    customer_account: Mapped["CustomerAccount"] = db.relationship(back_populates="customer")
    
    orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")
    
class CustomerAccount(Base):
    __tablename__ = "Customer_Accounts"
    account_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("Customers.customer_id"))
    customer: Mapped['Customer'] = db.relationship(back_populates="customer_account")

order_product = db.Table(
    "Order_Product",
    Base.metadata,
    db.Column("order_id", db.ForeignKey("Orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("Products.product_id"), primary_key=True)
)


class OrderProduct(Base):
    __tablename__ = "Order_Product"
    order_id = Column(Integer, ForeignKey('Orders.order_id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('Orders.product_id'), primary_key=True)

class Order(Base):
    __tablename__ = "Orders"
    order_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('Customers.customer_id'))
    customer: Mapped["Customer"] = db.relationship(back_populates="orders")
    products: Mapped[List["Product"]] = db.relationship(secondary= "order_product")

class Product(Base):
    __tablename__ = "Products"
    product_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)



 
with app.app_context(): 
    db.create_all()


# Schemas
class OrderProductSchema(ma.Schema):
    order_id = fields.Integer(required=True)
    product_id = fields.Integer(required=False)

    class Meta:
        fields = ("order_id", "product_id")

order_product_schema = OrderProductSchema()
order_products_schema = OrderProductSchema(many = True)

class CustomerSchema(ma.Schema):
    customer_id = fields.Integer(required=False)
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("customer_id", "name", "email", "phone")

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

class CustomerAccountSchema(ma.Schema):
    account_id = fields.Integer(required=False)
    username_id = fields.String(required = True)
    password = fields.String(required = True)
    customer_id = fields.Integer(required = True)
    class Meta:
        fields = ("account_id", "username", "password", "customer_id")

customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerAccountSchema(many = True)



class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ("product_id", "name", "price")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    customer_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    product_id = fields.List(fields.Integer())

    class Meta:
        fields = ("order_id", "customer_id", "date", "product_id")

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


# # ================ API ROUTES =========================


# #CUSTOMER
@app.route("/customers", methods = ["GET"])
def get_customers():
    #
    query = select(Customer) 
    result = db.session.execute(query).scalars() 
    print(result)
    customers = result
    for customer in result:
        for order in customer.orders:
            print(order.products)

   
    print(customers) 

    
    return customers_schema.jsonify(result)


@app.route("/customers", methods=["POST"])
def add_customer():
    try:
        
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin(): 
            name = customer_data['name']
            email = customer_data['email']
            phone = customer_data['phone']
            
            new_customer = Customer(name=name, email=email, phone=phone)
            
            session.add(new_customer)
            session.commit()
    return jsonify({"message": "New customer added successfully"}), 201

@app.route('/customers/<int:customer_id>', methods=["PUT"])
def updated_customer(customer_id):
    with Session(db.engine) as session: 
        with session.begin():  
            
            query = select(Customer).filter(Customer.customer_id == customer_id )
            result = session.execute(query).scalars().first()   
            if result is None:
                return jsonify({"error": "Customer not found"}), 404
            
            customer = result
           
            try:
                customer_data = customer_schema.load(request.json)

            except ValidationError as err:
                return jsonify(err.messages), 400
            
            
            for field, value in customer_data.items():
                setattr(customer, field, value)
            
            session.commit() 
            return jsonify({"message": "Customer details successfully updated"}), 200
        
@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    
    delete_statement = delete(Customer).where(Customer.customer_id==customer_id)
    with db.session.begin():
       
        result = db.session.execute(delete_statement)

        
        if result.rowcount==0: 
            return jsonify({"error": "Customer not found"}), 404
        
        return jsonify({"message": "Customer removed successfully!"})
    
# #PRODUCT

@app.route('/products', methods=["POST"])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    with Session(db.engine) as session:
        with session.begin():
            new_product = Product(name=product_data['name'], price=product_data['price'])
            session.add(new_product)
            session.commit()
    return jsonify({"Message": "New product successfully added!"}), 201 

@app.route('/products', methods=["GET"])
def get_products():
    query = select(Product) #SELECT * FROM Product
    result = db.session.execute(query).scalars()
    products = result.all()

    return products_schema.jsonify(products)


@app.route("/products/by-name", methods=["GET"])
def get_product_by_name():
    name = request.args.get("name")
    search = f"%{name}%" 
    query = select(Product).where(Product.name.like(search)).order_by(Product.price.asc())

    products = db.session.execute(query).scalars().all()
    print(products)

    return products_schema.jsonify(products)

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Product).filter(Product.product_id == product_id)
            result = session.execute(query).scalar() # the same as scalars().first() - first result in the scalars object
            print(result)            
            
            if result is None:
                return jsonify({"error": "Product not found!"}), 404
            product = result
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in product_data.items():
                setattr(product, field, value)

            session.commit()
            return jsonify({"message": "Product details successfully updated!"}), 200
        
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    delete_statement = delete(Product).where(Product.product_id==product_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error" "Product not found"}), 404
        
        return jsonify({"message": "Product successfully deleted!"}), 200
    


# #ORDER
@app.route("/orders", methods = ["POST"])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            new_order = Order(customer_id=order_data['customer_id'], date = order_data['date'])        
            
            session.add(new_order)            
            session.commit()          
            

    return jsonify({"message": "New order successfully added!"}), 201


@app.route("/orders", methods=["GET"])
def get_orders():
    query = select(Order)
    result = db.session.execute(query).scalars()
    return orders_schema.jsonify(result)

@app.route('/orders/<int:order_id>', methods=["PUT"])
def update_order(order_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Order).filter(Order.order_id==order_id)
            result = session.execute(query).scalar() #first result object
            if result is None:
                return jsonify({"message": "Product Not Found"}), 404
            order = result
            try:
                order_data = order_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in order_data.items():
                setattr(order, field, value)

            session.commit()
            return jsonify({"Message": "Order was successfully updated! "}), 200

@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    delete_statement = delete(Order).where(Order.order_id==order_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": "Order not found" }), 404
        return jsonify({"message": "Order removed successfully"}), 200

@app.route("/track_orders/<int:order_id>", methods=["TRACK"])
def track_order(order_id):
    order = Order.query.filter(Order.order_id == order_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    expected_delivery_date = order.date + timedelta(days=7)
    order_data = {
    "order_id": order.order_id,
    "date": order.date,
    "expected_delivery_date": expected_delivery_date, 
    "customer_id": order.customer_id,
    "status": "In progress"
    }
    return jsonify(order_data)

@app.route("/cancel_order/<int:order_id>", methods=["CANCEL"])   
def cancel_order(order_id):
    cancel_statement = cancel(Order).where(Order.order_id==order_id)
    with db.session.begin():
        result = db.session.execute(cancel_statement)
        if result.rowcount == 0:
            return jsonify({"error": "Order not found" }), 404
        return jsonify({"message": "Order canceled successfully"}), 200



# #ACCOUNT

@app.route("/customer_account", methods = ["GET"])
def get_customer_account():
    
    query = select(CustomerAccount) 
    result = db.session.execute(query).scalars() 
    print(result)
    customer_accounts = result.all()
    return customer_accounts_schema.jsonify(customer_accounts)

  

@app.route("/customers_account", methods=["POST"])
def add_customer_accounts():
    try:
        
        customer_accounts_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session: 
        with session.begin(): 
            username = customer_accounts_data['name']
            password = customer_accounts_data['email']
            customer_id = customer_accounts_data['phone']
            
            new_customer = Customer(username = username, password = password, customer_id = customer_id)
            session.add(new_customer)
            session.commit()
    return jsonify({"message": "New customer account added successfully"}), 201 

@app.route('/customers_accounts/<int:customer_id>', methods=["PUT"])
def updated_customer_accounts(customer_account_id):
    with Session(db.engine) as session: 
        with session.begin(): 
            
            query = select(CustomerAccount).filter(CustomerAccount.account_id == customer_account_id )
            result = session.execute(query).scalars().first()   
            if result is None:
                return jsonify({"error": "Customer account not found"}), 404
            
            customer_account = result 
            try:
                customer_account_data = customer_account_schema.load(request.json)

            except ValidationError as err:
                return jsonify(err.messages), 400
            
            
            for field, value in customer_account_data.items():
                setattr(customer_account, field, value)
            
            session.commit() 
            return jsonify({"message": "Customer's account details successfully updated"}), 200
        
@app.route("/customer_accounts/<int:customer_id>", methods=["DELETE"])
def delete_customer_account(customer_account_id):
    
    delete_statement = delete(Customer).where(Customer.customer_id==customer_account_id)
    with db.session.begin():
        
        result = db.session.execute(delete_statement)

        
        if result.rowcount==0: 
            return jsonify({"error": "Customer's account not found"}), 404
        
        return jsonify({"message": "Customer's account removed successfully!"})


    


    
             
















if __name__ == "__main__":
    app.run(debug=True)