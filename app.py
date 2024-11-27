from flask import Flask, render_template, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuring the SQLAlchemy Database URI for Windows Authentication
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://@MOHANAD\\SQLEXPRESS/Milestone2DB_24?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define a model for the customer_account table
class CustomerAccount(db.Model):
    __tablename__ = 'customer_account'
    mobileNo = db.Column(db.String(11), primary_key=True)
    password = db.Column('pass', db.String(50), nullable=False)
    balance = db.Column(db.Float)
    account_type = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    points = db.Column(db.Integer)
    nationalID = db.Column(db.Integer)

# Hardcoded admin credentials
ADMIN_ID = "123"
ADMIN_PASSWORD = "admin"

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Admin route
@app.route('/admin')
def admin():
    return render_template('admin.html')

# Customer route
@app.route('/customer')
def customer():
    return render_template('customer.html')

# Login route
@app.route('/login', methods=['POST'])
def login():
    login_type = request.form.get('login_type')
    username = request.form.get('admin_id') if login_type == 'admin' else request.form.get('mobile_number')
    password = request.form.get('password')

    if login_type == 'admin':
        # Check admin credentials
        if username == ADMIN_ID and password == ADMIN_PASSWORD:
            flash("Login successful! Redirecting to Admin Dashboard.", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid Admin ID or Password. Please try again.", "danger")
    else:
        # Check customer credentials from the database
        customer = CustomerAccount.query.filter_by(mobileNo=username, password=password).first()
        if customer:
            flash("Customer login successful! Redirecting to Customer Dashboard.", "success")
            return redirect(url_for('customer'))
        else:
            flash("Invalid Mobile Number or Password. Please try again.", "danger")

    return redirect(url_for('home'))

# View Customers route
@app.route('/view_customers')
def view_customers():
    try:
        query = text("SELECT * FROM allCustomerAccounts")
        result = db.session.execute(query)
        customers = result.fetchall()
        return render_template('view_customers.html', customers=customers)
    except Exception as e:
        flash(f"Error retrieving customers: {str(e)}", "danger")
        return redirect(url_for('admin'))

@app.route('/view_stores')
def view_stores():
    try:
        # Querying the PhysicalStoreVouchers view to get the list of all physical stores along with vouchers
        stores = db.session.execute(text('SELECT * FROM PhysicalStoreVouchers')).fetchall()
        return render_template('view_stores.html', stores=stores)
    except Exception as e:
        return f"Error retrieving physical stores and vouchers: {str(e)}"

# View Resolved Tickets route
@app.route('/view_resolved_tickets')
def view_resolved_tickets():
    try:
        # Query to get all resolved tickets from the view 'allResolvedTickets'
        resolved_tickets = db.session.execute(text('SELECT * FROM allResolvedTickets')).fetchall()
        
        return render_template('view_resolved_tickets.html', tickets=resolved_tickets)
    except Exception as e:
        flash(f"Error retrieving resolved tickets: {str(e)}", "danger")
        return render_template('view_resolved_tickets.html', tickets=None)
    
# View Customer Accounts and Subscribed Plans Route
@app.route('/view_customer_accounts')
def view_customer_accounts():
    try:
        # Executing the stored procedure to get account and plan details
        result = db.session.execute(text("EXEC Account_Plan;"))
        
        # Formatting the result to pass to the template
        accounts = []
        for row in result:
            accounts.append({
                "mobileNo": row.mobileNo,
                "account_type": row.account_type,
                "status": row.status,
                "start_date": row.start_date,
                "balance": row.balance,
                "points": row.points,
                "plan_name": row.name,
                "plan_price": row.price,
                "subscription_status": row.status
            })
        
        return render_template('view_customer_accounts.html', accounts=accounts)
    except Exception as e:
        return f"Error retrieving customer accounts: {str(e)}"

from sqlalchemy import text

@app.route('/list_accounts_by_plan', methods=['GET', 'POST'])
def list_accounts_by_plan():
    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        date = request.form.get('date')
        
        # Convert input date from DMY to YMD format
        try:
            parsed_date = datetime.strptime(date, "%d-%m-%Y")  # Assuming input date is in DD-MM-YYYY format
            formatted_date = parsed_date.strftime("%Y-%m-%d")   # Format to YYYY-MM-DD
        except ValueError:
            flash("Invalid date format. Please use DD-MM-YYYY.", "danger")
            return redirect(url_for('list_accounts_by_plan'))
        
        # Logic to fetch accounts based on plan_id and formatted_date
        try:
            query = f"SELECT * FROM dbo.Account_Plan_date('{formatted_date}', {plan_id})"
            results = db.session.execute(text(query)).fetchall()
            return render_template('list_accounts_by_plan.html', accounts=results, plan_id=plan_id, date=date)
        except Exception as e:
            flash(f"Error retrieving customer accounts: {str(e)}", "danger")
            return redirect(url_for('list_accounts_by_plan'))

    return render_template('list_accounts_by_plan.html', accounts=None)

# Show Total Usage of Input Account on Each Subscribed Plan from Input Date
@app.route('/show_account_usage', methods=['GET', 'POST'])
def show_account_usage():
    if request.method == 'POST':
        mobile_num = request.form.get('mobile_num')
        start_date = request.form.get('start_date')

        # Convert input date from DD-MM-YYYY to YYYY-MM-DD (SQL standard format)
        try:
            parsed_date = datetime.strptime(start_date, "%d-%m-%Y")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use the calendar to select the date.", "danger")
            return redirect(url_for('show_account_usage'))

        try:
            query = text("""
                SELECT planID, [total data], [total mins], [total SMS] 
                FROM dbo.Account_Usage_Plan(:mobile_num, :start_date)
            """)
            results = db.session.execute(query, {'mobile_num': mobile_num, 'start_date': formatted_date}).fetchall()

            return render_template('show_account_usage.html', usage=results, mobile_num=mobile_num, start_date=start_date)
        except Exception as e:
            flash(f"Error retrieving usage data: {str(e)}", "danger")
            return redirect(url_for('show_account_usage'))

    return render_template('show_account_usage.html', usage=None)

# Remove Benefits from Input Account for a Certain Plan ID
@app.route('/remove_benefits', methods=['GET', 'POST'])
def remove_benefits():
    if request.method == 'POST':
        mobile_number = request.form['mobile_number']
        plan_id = request.form['plan_id']

        try:
            # Prepare the query to call the stored procedure
            query = text("EXEC Benefits_Account @mobile_num=:mobile_number, @plan_id=:plan_id")

            # Execute the query with parameters
            db.session.execute(query, {'mobile_number': mobile_number, 'plan_id': plan_id})
            
            # Commit the transaction to make sure changes are applied
            db.session.commit()

            # If benefits were removed, flash a success message
            flash('Benefits successfully removed for the specified account and plan.', 'success')
        except Exception as e:
            # If there's an error, rollback the session and flash an error message
            db.session.rollback()
            flash(f'Error removing benefits: {str(e)}', 'danger')

    return render_template('remove_benefits.html')



# List All SMS Offers for a Certain Input Account
@app.route('/list_sms_offers', methods=['GET', 'POST'])
def list_sms_offers():
    if request.method == 'POST':
        mobile_num = request.form.get('mobile_num')

        try:
            # Query the Account_SMS_Offers function to retrieve SMS offers for the given mobile number
            query = text("SELECT * FROM dbo.Account_SMS_Offers(:mobile_num)")
            results = db.session.execute(query, {'mobile_num': mobile_num}).fetchall()
            
            # Render the HTML with the retrieved offers
            return render_template('list_sms_offers.html', sms_offers=results, mobile_num=mobile_num)
        except Exception as e:
            # Flash an error message and redirect to the same page in case of an error
            flash(f"Error retrieving SMS offers: {str(e)}", "danger")
            return redirect(url_for('list_sms_offers'))
    
    # Render the template without offers on the GET request
    return render_template('list_sms_offers.html', sms_offers=None)


if __name__ == '__main__':
    app.run(debug=True)
