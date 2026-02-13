#Milestone-0 VP-MAD-1
from flask import Flask,render_template,redirect,url_for,request
from flask_sqlalchemy import SQLAlchemy
from flask import session
from flask import flash
import os
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy.orm import joinedload
from datetime import datetime,timedelta
import io
import base64
import matplotlib.pyplot as plt



def create_app():
    app=Flask(__name__)
    app.config['SECRET_KEY']='app123'
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///parkingdata.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    app.config['CHART_FOLDER']=os.path.join('static','charts')
    os.makedirs(app.config['CHART_FOLDER'],exist_ok=True)
    app.config['PASSWORD_HASH']='app123'
    db.init_app(app)

    return app
db=SQLAlchemy()

class User(db.Model):
    __tablename__='user'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),unique=True,nullable=False)
    password=db.Column(db.String(120),nullable=False)
    fullname=db.Column(db.String(20),nullable=False)
    address=db.Column(db.String(20),nullable=False)
    pincode=db.Column(db.String(20),nullable=False)
    bookings=db.relationship('Booking',back_populates='user',cascade='all, delete-orphan')



class Parkinglot(db.Model):
    __tablename__='parking_lot'
    id=db.Column(db.Integer,primary_key=True)
    prime_locationname=db.Column(db.String(20),nullable=False)    
    address=db.Column(db.String(20),nullable=False)
    pin_code=db.Column(db.String(20),nullable=False)
    price=db.Column(db.Float,nullable=False)
    number_of_spots=db.Column(db.Integer,nullable=False)
    spots=db.relationship('Parkingspot',back_populates='parking',cascade='all, delete-orphan')
    



class Parkingspot(db.Model):
    __tablename__='parkingspot'
    id=db.Column(db.Integer,primary_key=True)
    parking_id=db.Column(db.Integer,db.ForeignKey('parking_lot.id'),nullable=False)
    spot_number=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(20),nullable=False,default='A')
    parking=db.relationship('Parkinglot',back_populates='spots')
    booking=db.relationship('Booking',back_populates='spot',cascade='all, delete-orphan')

class Booking(db.Model):
    __tablename__='booking'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    spot_id=db.Column(db.Integer,db.ForeignKey('parkingspot.id'),nullable=False)
    vehicle_number=db.Column(db.String(20),nullable=False)
    start_time=db.Column(db.DateTime,nullable=False)
    end_time=db.Column(db.DateTime,nullable=False)
    status=db.Column(db.String(20),nullable=False,default='A')
    parking_cost=db.Column(db.Float,nullable=False)
    user=db.relationship('User',back_populates='bookings')
    spot=db.relationship('Parkingspot',back_populates='booking')
def create_admin():
    admin=User.query.filter_by(username='admin1').first()
    if not admin:
        admin=User(username='admin1',password=generate_password_hash('admin1234'),fullname='admin',address='admin',pincode='admin')
        db.session.add(admin)
        db.session.commit()

app=create_app()
app.app_context().push()
with app.app_context():
    db.create_all()
    create_admin()





@app.route('/')
def index():
    return render_template('index.html')  
@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('admin_home'))
        else:
            return render_template('admin_login.html', error='Invalid username or password')
    return render_template('admin_login.html')

@app.route('/admin_home')
def admin_home():
    if 'username' not in session:
        return redirect(url_for('admin_login'))
     
    parking_lots = Parkinglot.query.options(joinedload(Parkinglot.spots)).all()

    for lot in parking_lots:
        lot.total = len(lot.spots)
        lot.occupied = sum(1 for spot in lot.spots if spot.status == 'O') 
    return render_template('admin_home.html', parking_lots=parking_lots)
    

@app.route('/admin_edit',methods=['GET','POST'])
def admin_edit():
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    if request.method=='POST':
        password=request.form['password']
        fullname=request.form['fullname']
        address=request.form['address']
        pincode=request.form['pincode']
        user=User.query.filter_by(username=session['username']).first()
        user.password=generate_password_hash(password)
        user.fullname=fullname
        user.address=address
        user.pincode=pincode
        db.session.commit()
        return redirect(url_for('admin_home'))
    return render_template('admin_edit.html')
@app.route("/add_lot",methods=['GET','POST'])
def add_lot():
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    if request.method=='POST':
        prime_locationname=request.form['prime_locationname']
        address=request.form['address']
        pin_code=request.form['pin_code']
        price=request.form['price']
        number_of_spots=request.form['number_of_spots']
        lot=Parkinglot(prime_locationname=prime_locationname,address=address,pin_code=pin_code,price=price,number_of_spots=number_of_spots)
        db.session.add(lot)
        db.session.commit()
        for i in range(1, int(number_of_spots)+1):
            spot = Parkingspot(parking_id=lot.id, spot_number=i, status='A')
            db.session.add(spot)
        db.session.commit()
        return redirect(url_for('admin_home'))
    return render_template('add_lot.html')
@app.route('/edit_lot/<int:lot_id>',methods=['GET','POST'])
def edit_lot(lot_id):
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    lot=Parkinglot.query.get_or_404(lot_id)
    if request.method=='POST':
        lot.prime_locationname=request.form['prime_locationname']
        lot.address=request.form['address']
        lot.pin_code=request.form['pin_code']
        lot.price=request.form['price']
        lot.number_of_spots=request.form['number_of_spots']
        db.session.commit()
        return redirect(url_for('admin_home'))
    return render_template('edit_lot.html',lot=lot)
@app.route('/delete_lot/<int:lot_id>',methods=['POST'])
def delete_lot(lot_id):
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    lot=Parkinglot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for('admin_home'))

@app.route('/view_spot/<int:spot_id>', methods=['GET', 'POST'])
def view_spot(spot_id):
    spot = Parkingspot.query.get_or_404(spot_id)
    if request.method == 'POST':
        if 'see_details' in request.form:
            if spot.status=='O':
                booking = Booking.query.filter_by(spot_id=spot.id, status='O').first()
                if booking:
                    return redirect(url_for('booking_details', spot_id=spot.id))
                flash('Spot marked occupied, but no active booking found.', 'WARNING!')
            return redirect(url_for('admin_home'))

        elif 'delete' in request.form:
            if spot.status == 'A':
                db.session.delete(spot)
                db.session.commit()
                flash('Spot deleted successfully.', 'success')
                return redirect(url_for('admin_home'))
            else:
                flash('Occupied spot cannot be deleted!', 'danger')

    return render_template('admin_view_spot.html', spot=spot)
@app.route('/booking_details/<int:spot_id>',methods=['GET','POST'])
def booking_details(spot_id):
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    spot=Parkingspot.query.get_or_404(spot_id)
    booking=Booking.query.filter_by(spot_id=spot.id,status='O').first()
    current_time=datetime.now()
    duration=(current_time - booking.start_time).total_seconds()/3600
    estimated_cost=round(duration*booking.parking_cost,2)
    if request.method == 'POST':
        return redirect(url_for('admin_home'))
    return render_template('admin_booking.html',spot=spot,booking=booking,estimated_cost=estimated_cost,current_time=current_time)

@app.route('/show_users')
def show_users():
    users=User.query.all()
    return render_template('admin_users.html',users=users)
@app.route('/edit_user/<int:user_id>',methods=['GET','POST'])
def edit_user(user_id):
    user=User.query.get_or_404(user_id)
    if request.method=='POST':
        user.username=request.form['username']
        user.fullname=request.form['fullname']
        user.address=request.form['address']
        user.pincode=request.form['pincode']
        db.session.commit()
        return redirect(url_for('show_users'))
    return render_template('admin_edit_user.html',user=user)

@app.route('/delete_user/<int:user_id>',methods=['POST'])
def delete_user(user_id):
    user=User.query.get_or_404(user_id)
    if user.bookings:
        flash('User has active bookings. Cannot delete.', 'danger')
        return redirect(url_for('show_users'))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('show_users'))

@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    results = []
    search_type = ''
    search_query = ''
    
    if request.method == 'POST':
        search_type = request.form['search_type']
        search_query = request.form['search_query'].strip()
        if search_type == 'lot':
            results = Parkinglot.query.options(joinedload(Parkinglot.spots)).filter(Parkinglot.address.ilike(f"%{search_query}%")).all()
            
        elif search_type == 'user':
            user = User.query.filter_by(id=search_query).first()
            if user:
                bookings = Booking.query.filter_by(user_id=user.id).all()
                enriched = []
                for booking in bookings:
                    spot = booking.spot
                    lot = spot.parking
                    enriched.append({
                        'booking': booking,
                        'spot': spot,
                        'lot': lot
                    })
                results = {'user': user, 'details': enriched}
        elif search_type == 'spot':
            spot = Parkingspot.query.get(search_query)
            if spot:
                results = {'spot': spot, 'lot': spot.parking}

    return render_template('admin_search.html',results=results,search_type=search_type,query=search_query)

def create_pie_chart(revenues,labels):
    import math

    if all(r == 0 or r is None or math.isnan(r) for r in revenues):
        return None 

    cleaned = [r if r is not None and not math.isnan(r) else 0 for r in revenues]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(revenues,labels=labels,autopct='%1.1f%%',startangle=140)
    ax.set_title('REVENUE CONTRIBUTION BY PARKING LOTS')

    img = io.BytesIO()
    plt.savefig(img,format='png')
    img.seek(0)
    pie_url = base64.b64encode(img.read()).decode('utf8')
    plt.close()
    return pie_url
def create_bar_chart(available, occupied, labels):
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x, available, width=0.4, label='Available', align='center', color='lightgreen')
    ax.bar(x, occupied, width=0.4, label='Occupied', align='edge', color='salmon')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel('Number of Spots')
    ax.set_title('Availability vs Occupied Spots')
    ax.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    bar_url = base64.b64encode(img.read()).decode('utf8')
    plt.close()
    return bar_url
@app.route('/admin_summary')
def admin_summary():
    lots=Parkinglot.query.options(joinedload(Parkinglot.spots)).all()
    labels=[]
    revenues=[]
    available=[]
    occupied=[]
    for lot in lots:
        labels.append(lot.address)
        lot_revenue=sum(booking.parking_cost for spot in lot.spots for booking in spot.booking if booking.status=='O')
        revenues.append(lot_revenue)
        avail=sum(1 for spot in lot.spots if spot.status=='A')
        occup=sum(1 for spot in lot.spots if spot.status=='O')
        available.append(avail)
        occupied.append(occup)
        pie_img=create_pie_chart(revenues,labels)
        bar_img=create_bar_chart(available,occupied,labels)
    return render_template('admin_summary.html',pie_img=pie_img,bar_img=bar_img)
           
    



@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']   
        password=request.form['password']
        user=User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            session['username']=username
            session['user_id']=user.id
            return redirect(url_for('user_home'))
        else:
            return render_template('user_login.html',error='Invalid username or password')
    return render_template('user_login.html')
            
            
@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        username=request.form['username']
        fullname=request.form['fullname']
        address=request.form['address']
        pincode=request.form['pincode']
        password=request.form['password']
        user=User(username=username,fullname=fullname,address=address,pincode=pincode,password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit() 
        return redirect(url_for('login'))
    return render_template('signup.html') 
@app.route('/user_home')
def user_home():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_id=session['user_id']
    active_bookings=[booking for booking in Booking.query.filter_by(user_id=user_id).all() if booking.status=='O']
    released_bookings=[booking for booking in Booking.query.filter_by(user_id=user_id).all() if booking.status=='A']
    return render_template('user_home.html',active_bookings=active_bookings,released_bookings=released_bookings)
@app.route('/user_edit')
def user_edit():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('user_edit.html')
@app.route('/user_search',methods=['GET','POST'])
def user_search():
    if 'username' not in session:
        return redirect(url_for('login'))
    results=[]
    search_type=''
    search_query=''
    if request.method=='POST':
        search_type=request.form['search_type']
        search_query=request.form['search_query'].strip()
        if search_type=='address':
             results = Parkinglot.query.filter(Parkinglot.address.ilike(f"%{search_query}%")).all()
        elif search_type=='pincode':
            results = Parkinglot.query.filter(Parkinglot.pin_code == search_query).all()
        db.session.expire_all()    
        for lot in results:
            available = Parkingspot.query.filter_by(parking_id=lot.id, status='A').count()
            lot.available_spots = available
    return render_template('user_search.html',results=results,search_type=search_type,search_query=search_query)

@app.route('/release_form/<int:booking_id>')
def release_form(booking_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    release_time = datetime.now()
    duration = (release_time - booking.start_time).total_seconds()
    price = booking.spot.parking.price
    total_cost = round((duration / 3600) * price, 2)

    return render_template('user_release_clean.html',
        booking=booking,
        release_time_str=release_time.strftime('%Y-%m-%d %H:%M:%S'),
        total_cost=total_cost
    )
@app.route('/release_confirm/<int:booking_id>',methods=['POST'])
def release_confirm(booking_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    booking = Booking.query.get_or_404(booking_id)
    booking.spot.status = 'A'
    booking.status = 'A'
    db.session.commit()
    return redirect(url_for('user_home'))

@app.route('/user_book/<int:lot_id>', methods=['POST'])
def book_parking(lot_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    lot = Parkinglot.query.get_or_404(lot_id)
    
    available_spot = next((spot for spot in lot.spots if spot.status == 'A'), None)
    if not available_spot:
        flash('No available spots', 'danger')
        return redirect(url_for('user_home'))

    vehicle_number = f"xyz{user_id}"
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=2)
    parking_cost = lot.price

    available_spot.status = 'O'  

    new_booking = Booking(
        user_id=user_id,
        spot_id=available_spot.id,
        vehicle_number=vehicle_number,
        start_time=start_time,
        end_time=end_time,
        status='O',
        parking_cost=parking_cost
    )

    db.session.add(new_booking)
    db.session.commit()

    flash('Booking successful', 'success')
    return redirect(url_for('user_home'))
from collections import defaultdict
@app.route('/user_summary')
def user_summary():
    if 'username' not in session:
        return redirect(url_for('login'))
    user=User.query.filter_by(username=session['username']).first()
    booking=Booking.query.filter_by(user_id=user.id).all()
    lot_duration=defaultdict(float)
    for book in booking:
        lot_name=book.spot.parking.address
        start=book.start_time
        if book.status=="O":
            end=datetime.now()
        else:
            end=book.end_time
        duration=(end-start).total_seconds()/3600
        lot_duration[lot_name]+=duration
    labels=list(lot_duration.keys())
    values=[round(v,2) for v in lot_duration.values()]

    fig,ax=plt.subplots(figsize=(5,5))
    ax.bar(labels,values,color='skyblue')
    ax.set_xlabel('PARKING LOT')
    ax.set_ylabel('TIME SPENT(IN HOURS)')
    ax.set_title('TIME SPENT AT EACH PARKING LOT TILL NOW!') 

    plt.xticks(rotation=30,ha='right')
    plt.tight_layout()

    img=io.BytesIO()
    plt.savefig(img,format='png')
    img.seek(0)

    chart=base64.b64encode(img.read()).decode('utf8')  
    return render_template('user_summary.html',chart=chart)         

@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('user_id',None)
    return render_template('index.html')





if __name__=='__main__':
    app.run(debug=True)
