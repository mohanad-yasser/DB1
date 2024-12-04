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
    
from sqlalchemy import text

# View Customer Accounts and Subscribed Plans Route
@app.route('/view_customer_accounts')
def view_customer_accounts():
    try:
        # Executing the stored procedure to get account and plan details
        result = db.session.execute(text("""
            EXEC Account_Plan;
        """))

        # Extracting the column names (to confirm order)
        columns = result.keys()
        accounts = []

        # Fetch the result and process it
        rows = result.fetchall()  # Fetch the rows only once
        print("Database result:", rows)  # <-- Debug print to check raw data

        for row in rows:
            # Creating a dictionary to match the columns from the result
            account = {
                "mobileNo": row[0],           # customer_account.mobileNo
                "pass": row[1],               # customer_account.pass
                "balance": row[2],            # customer_account.balance
                "account_type": row[3],       # customer_account.account_type
                "start_date": row[4],         # customer_account.start_date
                "status": row[5],             # customer_account.status
                "points": row[6],             # customer_account.points
                "nationalID": row[7],         # customer_account.nationalID
                "planID": row[8],             # Service_plan.planID
                "name": row[9],               # Service_plan.name
                "price": row[10],             # Service_plan.price
                "SMS_offered": row[11],       # Service_plan.SMS_offered
                "minutes_offered": row[12],   # Service_plan.minutes_offered
                "data_offered": row[13],      # Service_plan.data_offered
                "description": row[14]        # Service_plan.description
            }
            accounts.append(account)

        print("Accounts being passed to template:", accounts)  # <-- Debug print

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

@app.route('/show_account_usage', methods=['GET', 'POST'])
def account_usage():
    if request.method == 'POST':
        mobile_no = request.form['mobileNo']
        start_date = request.form['start_date']
        
        # Parse the date in DD-MM-YYYY format to YYYY-MM-DD for SQL
        try:
            formatted_date = datetime.strptime(start_date, '%d-%m-%Y').date()
        except ValueError:
            return "Invalid date format. Please use DD-MM-YYYY.", 400
        
        # Execute the function in the database with the provided date
        result = db.session.execute(
            text("SELECT * FROM Account_Usage_Plan(:mobile_no, :start_date)"),
            {'mobile_no': mobile_no, 'start_date': formatted_date}
        ).fetchall()
        
        # Convert result into a list of dictionaries
        usage_data = [
            {
                'planID': row[0],
                'total_data': row[1],
                'total_mins': row[2],
                'total_sms': row[3]
            }
            for row in result
        ]

        # Return the template with the data
        return render_template('show_account_usage.html', usage_data=usage_data, mobile_num=mobile_no, start_date=start_date)

    return render_template('show_account_usage.html')

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

# View all wallets along with customer names
@app.route('/view_wallets')
def view_wallets():
    try:
        # Query to fetch wallet details along with customer names from the CustomerWallet view
        query = text("SELECT * FROM CustomerWallet")
        result = db.session.execute(query)
        wallets = result.fetchall()

        # Render the template with the wallet data
        return render_template('view_wallets.html', wallets=wallets)
    except Exception as e:
        flash(f"Error retrieving wallet details: {str(e)}", "danger")
        return redirect(url_for('admin'))

@app.route('/view_eshops')
def view_eshops():
    try:
        # Query to fetch E-shop details along with redeemed voucher IDs and values
        query = text('SELECT * FROM E_shopVouchers')
        result = db.session.execute(query)
        eshops = result.fetchall()
        return render_template('view_eshops.html', eshops=eshops)
    except Exception as e:
        flash(f"Error retrieving E-shops or vouchers: {str(e)}", "danger")
        return redirect(url_for('admin'))

@app.route('/view_all_payments')
def view_all_payments():
    try:
        # Query the AccountPayments view to fetch all payment transactions along with account details
        payments = db.session.execute(text("SELECT * FROM AccountPayments")).fetchall()
        return render_template('view_all_payments.html', payments=payments)
    except Exception as e:
        flash(f"Error retrieving payment transactions: {str(e)}", "danger")
        return redirect(url_for('admin'))

@app.route('/view_cashback_transactions')
def view_cashback_transactions():
    try:
        # Query the Num_of_cashback view to fetch the count of cashback transactions per wallet
        cashback_counts = db.session.execute(text("SELECT * FROM Num_of_cashback")).fetchall()
        return render_template('view_cashback_transactions.html', cashback_counts=cashback_counts)
    except Exception as e:
        flash(f"Error retrieving cashback transaction data: {str(e)}", "danger")
        return redirect(url_for('admin'))
    
@app.route('/view_accepted_payments', methods=['GET', 'POST'])
def view_accepted_payments():
    payment_count = None
    total_points = None

    if request.method == 'POST':
        mobile_num = request.form['mobile_num']

        try:
            # Debugging: Print mobile number received from the form
            print(f"Mobile Number Received: {mobile_num}")

            # Executing the query with parameter binding
            query = text("""
                EXEC Account_Payment_Points @mobile_num=:mobile_num
            """)
            result = db.session.execute(query, {'mobile_num': mobile_num}).fetchone()

            # Debugging: Check if result is None or not
            if result:
                # Extracting the result values
                payment_count = result[0]  # Number of successful payments
                total_points = result[1]   # Total points earned
                
                # Debugging: Print the result values
                print(f"Payment Count: {payment_count}, Total Points: {total_points}")

                flash("Data fetched successfully!", "success")
            else:
                flash("No successful payments found for this mobile number in the last year.", "danger")
                
                # Debugging: Print message when no data is found
                print("No successful payments found for this mobile number in the last year.")
            
        except Exception as e:
            flash(f"Error fetching data: {str(e)}", "danger")
            # Ensure no data is passed in case of error
            payment_count = None
            total_points = None

            # Debugging: Print the exception if there's an error
            print(f"Error fetching data: {str(e)}")

        # Debugging: Print the values being passed to the template
        print(f"Passing to template: payment_count = {payment_count}, total_points = {total_points}")

        # Rendering the template with data passed
        return render_template('view_accepted_payments.html', 
                               payment_count=payment_count, 
                               total_points=total_points)

    # For GET request, just render the empty form and the empty results
    return render_template('view_accepted_payments.html', payment_count=None, total_points=None)

@app.route('/view_cashback_by_wallet_and_plan', methods=['GET', 'POST'])
def view_cashback_by_wallet_and_plan():
    if request.method == 'POST':
        wallet_id = request.form['wallet_id']
        plan_id = request.form['plan_id']
        
        try:
            # Execute the Wallet_Cashback_Amount function with parameter binding
            query = text("""
                SELECT dbo.Wallet_Cashback_Amount(:wallet_id, :plan_id)
            """)
            result = db.session.execute(query, {'wallet_id': wallet_id, 'plan_id': plan_id}).fetchone()

            # Check if result is None or not
            if result:
                cashback_amount = result[0]  # Cashback amount returned by the function
                flash("Data fetched successfully!", "success")
            else:
                cashback_amount = None
                flash("No cashback found for this wallet and plan combination.", "danger")
            
        except Exception as e:
            flash(f"Error fetching data: {str(e)}", "danger")
            cashback_amount = None

        # Rendering the template with the cashback amount data passed
        return render_template('view_cashback_by_wallet_and_plan.html', cashback_amount=cashback_amount)

    # For GET request, just render the empty form and the empty results
    return render_template('view_cashback_by_wallet_and_plan.html', cashback_amount=None)

@app.route('/view_avg_transfer', methods=['GET', 'POST'])
def view_avg_transfer():
    if request.method == 'POST':
        wallet_id = request.form['wallet_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        try:
            # Manually parsing MM-DD-YYYY format to YYYY-MM-DD
            parsed_start_date = datetime.strptime(start_date, "%m-%d-%Y") if start_date else None
            parsed_end_date = datetime.strptime(end_date, "%m-%d-%Y") if end_date else None

            # Convert to string format (YYYY-MM-DD)
            formatted_start_date = parsed_start_date.strftime("%Y-%m-%d") if parsed_start_date else None
            formatted_end_date = parsed_end_date.strftime("%Y-%m-%d") if parsed_end_date else None

        except ValueError:
            flash("Invalid date format. Please use MM-DD-YYYY.", "danger")
            return redirect(url_for('view_avg_transfer'))

        try:
            # Query to call the Wallet_Transfer_Amount function
            query = text("""
                SELECT dbo.Wallet_Transfer_Amount(:wallet_id, :start_date, :end_date) AS avg_transfer_amount
            """)
            result = db.session.execute(query, {
                'wallet_id': wallet_id, 
                'start_date': formatted_start_date, 
                'end_date': formatted_end_date
            }).fetchone()

            # Check if result is None
            if result:
                avg_transfer_amount = result[0]
                flash("Data fetched successfully!", "success")
            else:
                avg_transfer_amount = None
                flash("No transactions found for this wallet within the given date range.", "danger")

        except Exception as e:
            flash(f"Error fetching data: {str(e)}", "danger")
            avg_transfer_amount = None

        return render_template('view_avg_transfer.html', avg_transfer_amount=avg_transfer_amount)

    # For GET request, render the empty form
    return render_template('view_avg_transfer.html', avg_transfer_amount=None)

@app.route('/check_wallet_linkage', methods=['GET', 'POST'])
def check_wallet_linkage():
    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Getting the mobile number from the form

        try:
            # Execute the SQL query using the Wallet_MobileNo function
            query = text("""
                SELECT dbo.Wallet_MobileNo(:mobile_num) AS is_linked
            """)
            result = db.session.execute(query, {'mobile_num': mobile_num}).fetchone()

            # Check if the result is returned as 1 or 0
            if result:
                is_linked = result[0]
                if is_linked == 1:
                    flash(f"The mobile number {mobile_num} is linked to a wallet.", "success")
                else:
                    flash(f"The mobile number {mobile_num} is not linked to any wallet.", "danger")
            else:
                flash("Error checking wallet linkage.", "danger")

        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

        return render_template('check_wallet_linkage.html', is_linked=is_linked)

    return render_template('check_wallet_linkage.html', is_linked=None)

@app.route('/update_points', methods=['GET', 'POST'])
def update_points():
    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Get mobile number from the form
        
        try:
            # Execute the stored procedure to update points for the mobile number
            query = text("""
                EXEC dbo.Total_Points_Account :mobile_num
            """)
            result = db.session.execute(query, {'mobile_num': mobile_num})
            
            # Flash success message
            flash(f"Points updated successfully for mobile number {mobile_num}.", "success")
        
        except Exception as e:
            flash(f"Error updating points: {str(e)}", "danger")
    
        return render_template('update_points.html')

    return render_template('update_points.html')

@app.route('/view_service_plans')
def view_service_plans():
    try:
        # Query to fetch all service plans from the database
        query = text("SELECT * FROM allServicePlans")
        result = db.session.execute(query).fetchall()

        # Render the template with the service plans data
        return render_template('view_service_plans.html', service_plans=result)
    except Exception as e:
        # Flash an error message if there is a problem
        flash(f"Error retrieving service plans: {str(e)}", "danger")
        
        # Render the template again with the error message, keeping the user on the same page
        return render_template('view_service_plans.html', service_plans=None)
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for
from sqlalchemy import text

@app.route('/view_consumption', methods=['GET', 'POST'])
def view_total_consumption():
    if request.method == 'POST':
        plan_name = request.form['plan_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Convert input dates from MM-DD-YYYY to YYYY-MM-DD format
        try:
            parsed_start_date = datetime.strptime(start_date, "%m-%d-%Y")
            parsed_end_date = datetime.strptime(end_date, "%m-%d-%Y")
            formatted_start_date = parsed_start_date.strftime("%Y-%m-%d")
            formatted_end_date = parsed_end_date.strftime("%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use MM-DD-YYYY.", "danger")
            return redirect(url_for('view_consumption'))

        # Query the Consumption function
        try:
            query = text("""
                SELECT * 
                FROM dbo.Consumption(:plan_name, :start_date, :end_date)
            """)
            # Execute the query and fetch the result
            result = db.session.execute(query, {
                'plan_name': plan_name,
                'start_date': formatted_start_date,
                'end_date': formatted_end_date
            }).fetchone()

            # Check if the result is not None and contains data
            if result:
                total_consumption = {
                    "data_consumption": result[0],  # Access by index (0 = data_consumption)
                    "minutes_used": result[1],       # Access by index (1 = minutes_used)
                    "SMS_sent": result[2]            # Access by index (2 = SMS_sent)
                }
            else:
                total_consumption = None
                flash("No consumption data found for this plan and date range.", "danger")

            return render_template('view_consumption.html', total_consumption=total_consumption)

        except Exception as e:
            flash(f"Error retrieving consumption data: {str(e)}", "danger")
            return redirect(url_for('view_total_consumption'))

    return render_template('view_consumption.html', total_consumption=None)

@app.route('/view_unsubscribed_plans', methods=['GET', 'POST'])
def view_unsubscribed_plans():
    unsubscribed_plans = None  # Default to None in case no plans are found

    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Get mobile number from the form

        # Validate mobile number format (assuming it's an 11-digit string)
        if len(mobile_num) != 11 or not mobile_num.isdigit():
            flash("Please enter a valid mobile number.", "danger")
            return redirect(url_for('view_unsubscribed_plans'))

        try:
            # Query the Unsubscribed_Plans procedure
            query = text("""
                EXEC Unsubscribed_Plans @mobile_num=:mobile_num
            """)
            result = db.session.execute(query, {'mobile_num': mobile_num}).fetchall()

            if result:
                unsubscribed_plans = result
            else:
                flash("No unsubscribed plans found for this customer.", "warning")

        except Exception as e:
            flash(f"Error retrieving unsubscribed plans: {str(e)}", "danger")

    return render_template('view_unsubscribed_plans.html', unsubscribed_plans=unsubscribed_plans)

@app.route('/view_account_usage', methods=['GET', 'POST'])
def view_account_usage():
    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Get mobile number from the form

        # Validate mobile number format (assuming it's an 11-digit string)
        if len(mobile_num) != 11 or not mobile_num.isdigit():
            flash("Please enter a valid mobile number.", "danger")
            return redirect(url_for('view_account_usage'))

        try:
            # Query to execute the Usage_Plan_CurrentMonth function
            query = text("""
                SELECT * 
                FROM dbo.Usage_Plan_CurrentMonth(:mobile_num)
            """)
            # Execute the query and fetch the result
            result = db.session.execute(query, {'mobile_num': mobile_num}).fetchall()

            if result:
                usage_data = [{
                    "data_consumption": row[0],
                    "minutes_used": row[1],
                    "SMS_sent": row[2]
                } for row in result]

                return render_template('view_account_usage.html', usage_data=usage_data, mobile_num=mobile_num)
            else:
                flash("No active plans found for this mobile number in the current month.", "warning")
                return render_template('view_account_usage.html', usage_data=None)

        except Exception as e:
            flash(f"Error retrieving usage data: {str(e)}", "danger")
            return render_template('view_account_usage.html', usage_data=None)

    return render_template('view_account_usage.html', usage_data=None)

@app.route('/view_customer_cashbacks', methods=['GET', 'POST'])
def view_customer_cashbacks():
    if request.method == 'POST':
        national_id = request.form['national_id']  # Get the National ID from the form

        try:
            # Query to execute the Cashback_Wallet_Customer function
            query = text("""
                SELECT * FROM Cashback_Wallet_Customer(:national_id)
            """)
            # Execute the query and fetch the results
            result = db.session.execute(query, {'national_id': national_id}).fetchall()

            # If there are results, process them and pass to the template
            if result:
                cashback_transactions = [{
                    "transaction_id": row[0],
                    "wallet_id": row[1],
                    "amount": row[2],
                    "transaction_date": row[3],
                    "description": row[4]
                } for row in result]

                flash("Cashback transactions fetched successfully!", "success")
                return render_template('view_customer_cashbacks.html', cashback_transactions=cashback_transactions, national_id=national_id)
            else:
                flash("No cashback transactions found for this National ID.", "danger")
                return render_template('view_customer_cashbacks.html', cashback_transactions=None)

        except Exception as e:
            flash(f"Error fetching cashback transactions: {str(e)}", "danger")
            return render_template('view_customer_cashbacks.html', cashback_transactions=None)

    return render_template('view_customer_cashbacks.html', cashback_transactions=None)

@app.route('/view_active_benefits', methods=['GET', 'POST'])
def view_active_benefits():
    try:
        # Query the 'allBenefits' view to fetch active benefits
        query = text("SELECT * FROM allBenefits")
        result = db.session.execute(query).fetchall()

        # Check if there are any results and pass to template
        if result:
            benefits = [{
                "benefitID": row[0],  # benefitID
                "description": row[1],  # description
                "validity_date": row[2],  # validity_date
                "status": row[3],  # status
                "mobileNo": row[4]  # mobileNo
            } for row in result]

            return render_template('view_active_benefits.html', benefits=benefits)
        else:
            flash("No active benefits found.", "warning")
            return render_template('view_active_benefits.html', benefits=None)
    
    except Exception as e:
        flash(f"Error retrieving active benefits: {str(e)}", "danger")
        return render_template('view_active_benefits.html', benefits=None)
    
@app.route('/view_unresolved_tickets', methods=['GET', 'POST'])
def view_unresolved_tickets():
    unresolved_tickets = None  # Default to None in case no tickets are found

    if request.method == 'POST':
        # Get National ID from the form
        national_id = request.form['national_id']

        # Validate National ID (assuming it's an integer)
        try:
            national_id = int(national_id)
        except ValueError:
            flash("Please enter a valid National ID.", "danger")
            return redirect(url_for('view_unresolved_tickets'))

        try:
            # Query the Ticket_Account_Customer stored procedure to get unresolved tickets
            query = text("""
                EXEC Ticket_Account_Customer @NID=:national_id
            """)
            result = db.session.execute(query, {'national_id': national_id}).fetchone()

            # Check if result is not None
            if result:
                unresolved_tickets = result[0]  # Extract count of unresolved tickets
            else:
                flash("No unresolved tickets found for this National ID.", "warning")

        except Exception as e:
            flash(f"Error retrieving unresolved tickets: {str(e)}", "danger")

    return render_template('view_unresolved_tickets.html', unresolved_tickets=unresolved_tickets)

# Define the route to view highest voucher for a customer
@app.route('/view_highest_voucher', methods=['GET', 'POST'])
def view_highest_voucher():
    voucher_info = None

    if request.method == 'POST':
        mobile_num = request.form['mobile_num']

        # Validate the mobile number format
        if len(mobile_num) != 11 or not mobile_num.isdigit():
            flash("Please enter a valid 11-digit mobile number.", "danger")
            return redirect(url_for('view_highest_voucher'))

        try:
            # Execute stored procedure to get the highest value voucher
            query = text("""
                EXEC Account_Highest_Voucher :mobile_num
            """)
            result = db.session.execute(query, {'mobile_num': mobile_num}).fetchall()

            # If the procedure returns a voucher ID, display it
            if result:
                voucher_info = result[0]  # Extract the voucherID
                flash(f"Voucher ID with the highest value: {voucher_info[0]}", "success")
            else:
                flash("No vouchers found for this account.", "warning")

        except Exception as e:
            flash(f"Error retrieving voucher: {str(e)}", "danger")
            return redirect(url_for('view_highest_voucher'))

    return render_template('view_highest_voucher.html', voucher_info=voucher_info)

@app.route('/remaining_plan_amount', methods=['GET', 'POST'])
def remaining_plan_amount():
    remaining_amount = None

    if request.method == 'POST':
        mobile_num = request.form['mobile_num']
        plan_name = request.form['plan_name']

        # Validate the mobile number format
        if len(mobile_num) != 11 or not mobile_num.isdigit():
            flash("Please enter a valid 11-digit mobile number.", "danger")
            return redirect(url_for('remaining_plan_amount'))

        try:
            # Execute the stored function to get the remaining amount for the plan
            query = text("""
                SELECT dbo.Remaining_plan_amount(:mobile_num, :plan_name) AS remaining_amount
            """)
            result = db.session.execute(query, {'mobile_num': mobile_num, 'plan_name': plan_name}).fetchone()

            if result:
                remaining_amount = result[0]
                if remaining_amount is not None:
                    flash(f"Remaining Amount for plan '{plan_name}': {remaining_amount}", "success")
                else:
                    flash(f"No remaining amount found for the given plan and account.", "warning")
            else:
                flash("No data found for the given mobile number or plan.", "warning")

        except Exception as e:
            flash(f"Error retrieving data: {str(e)}", "danger")

    return render_template('remaining_plan_amount.html', remaining_amount=remaining_amount)

@app.route('/get_extra_amount', methods=['GET', 'POST'])
def get_extra_amount():
    extra_amount = None

    if request.method == 'POST':
        mobile_no = request.form.get('mobile_no')
        plan_name = request.form.get('plan_name')

        # Query to fetch the extra amount using the previously created SQL function
        try:
            # Use dict() to fetch the result as a dictionary
            query = text("""
                SELECT dbo.Extra_plan_amount(:mobile_no, :plan_name) AS extra_amount
            """)

            # Fetch the result and return as a dictionary
            result = db.session.execute(query, {'mobile_no': mobile_no, 'plan_name': plan_name}).fetchone()

            # result should be a tuple (if using fetchone), so we need to access it by index, not string keys
            if result:
                # Since we're using fetchone(), it's a tuple, so access it by index
                extra_amount = result[0]  # result[0] contains the extra_amount value
            else:
                flash('No data found or error occurred.', 'danger')

        except Exception as e:
            flash(f"Error retrieving extra amount: {str(e)}", 'danger')

    return render_template('get_extra_amount.html', extra_amount=extra_amount)

@app.route('/top_successful_payments', methods=['GET', 'POST'])
def top_successful_payments():
    top_payments = []

    if request.method == 'POST':
        mobile_no = request.form.get('mobile_no')

        try:
            # Call the stored procedure to get the top 10 successful payments
            query = text("""
                EXEC Top_Successful_Payments :mobile_no
            """)

            # Execute the query and fetch the results
            result = db.session.execute(query, {'mobile_no': mobile_no}).fetchall()

            # If results exist, prepare them for display
            if result:
                for row in result:
                    top_payments.append({
                        "paymentID": row.paymentID,
                        "amount": row.amount,
                        "date_of_payment": row.date_of_payment,
                        "payment_method": row.payment_method,
                        "status": row.status,
                        "mobile_no":row.mobileNo
                    })
            else:
                flash("No successful payments found for this mobile number.", "danger")

        except Exception as e:
            flash(f"Error retrieving top payments: {str(e)}", "danger")

    return render_template('top_successful_payments.html', top_payments=top_payments)

@app.route('/view_shops')
def view_shops():
    try:
        # Query the 'allShops' view to get all shop details
        query = text('SELECT * FROM allShops')
        result = db.session.execute(query).fetchall()

        # Check if there are any shops, and if so, prepare the list
        shops = []
        for row in result:
            shops.append({
                "shopID": row.shopID,
                "name": row.name,
                "category": row.Category
            })
        
        # Render the template and pass the shop details
        return render_template('view_shops.html', shops=shops)
    
    except Exception as e:
        # Flash an error message if something goes wrong
        flash(f"Error retrieving shops: {str(e)}", "danger")
        return render_template('view_shops.html', shops=None)

# Define the route to view all subscribed plans in the past 5 months
@app.route('/view_subscribed_plans', methods=['POST', 'GET'])
def view_subscribed_plans():
    if request.method == 'POST':
        mobile_num = request.form.get('mobile_num')  # Get mobile number from the form
        
        try:
            # Call the function to retrieve subscribed plans
            query = text("""
                SELECT planID, name, price, SMS_offered, minutes_offered, data_offered, description
                FROM dbo.Subscribed_plans_5_Months(:mobile_num)
            """)
            # Execute the query with the provided mobile number
            result = db.session.execute(query, {'mobile_num': mobile_num}).fetchall()
            
            # Check if we got results
            if result:
                # If plans are found, pass them to the template
                plans = [{'planID': row[0], 'name': row[1], 'price': row[2], 
                          'SMS_offered': row[3], 'minutes_offered': row[4], 
                          'data_offered': row[5], 'description': row[6]} for row in result]
                return render_template('view_subscribed_plans.html', plans=plans)
            else:
                flash("No plans found in the past 5 months for this account.", "danger")
                return redirect(url_for('view_subscribed_plans'))
        
        except Exception as e:
            flash(f"Error retrieving subscribed plans: {str(e)}", "danger")
            return redirect(url_for('view_subscribed_plans'))

    return render_template('view_subscribed_plans.html', plans=None)

@app.route('/renew_subscription', methods=['POST', 'GET'])
def renew_subscription():
    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Mobile number input
        plan_id = request.form['plan_id']        # Plan ID input
        amount = request.form['amount']          # Payment amount
        payment_method = request.form['payment_method']  # Payment method (cash/credit)

        try:
            # Ensure the data is valid
            if not mobile_num or not plan_id or not amount or not payment_method:
                flash("All fields are required.", "danger")
                return render_template('renew_subscription.html')
            
            # Execute the stored procedure to process the renewal
            query = text("""
                EXEC Initiate_plan_payment :mobile_num, :amount, :payment_method, :plan_id
            """)
            
            # Execute query with the provided parameters
            db.session.execute(query, {
                'mobile_num': mobile_num,
                'amount': float(amount),  # Ensure it's treated as a float
                'payment_method': payment_method,
                'plan_id': int(plan_id)   # Ensure it's treated as an integer
            })
            
            # Commit the transaction if everything goes well
            db.session.commit()

            flash("Subscription renewed successfully!", "success")
        except Exception as e:
            # Rollback the transaction if an error occurs
            db.session.rollback()
            flash(f"Error occurred while processing payment: {str(e)}", "danger")
        
    # In both cases (success or failure), return the same page with any flash messages
    return render_template('renew_subscription.html')

@app.route('/payment_wallet_cashback', methods=['POST', 'GET'])
def payment_wallet_cashback():
    cashback_amount = None

    if request.method == 'POST':
        mobile_no = request.form.get('mobile_num')
        payment_id = request.form.get('payment_id')
        benefit_id = request.form.get('benefit_id')

        try:
            # Execute the stored procedure to calculate cashback
            query = text("""
                EXEC Payment_wallet_cashback :mobile_num, :payment_id, :benefit_id
            """)

            # Execute the query with the provided parameters
            db.session.execute(query, {
                'mobile_num': mobile_no,
                'payment_id': payment_id,
                'benefit_id': benefit_id
            })

            # Commit the transaction
            db.session.commit()

            # Calculate cashback (fixed logic, can also be done inside the stored procedure if needed)
            # Query the database for the amount (this can be modified based on how you store it)
            query = text("""
                SELECT 0.1 * p.amount
                FROM Payment p
                WHERE p.paymentID = :payment_id AND p.status = 'successful'
            """)
            result = db.session.execute(query, {'payment_id': payment_id}).fetchone()

            if result:
                cashback_amount = result[0]  # Extract the cashback value from the query result
            else:
                flash("No valid payment found.", "danger")

        except Exception as e:
            flash(f"Error occurred while processing cashback: {str(e)}", "danger")
    
    # Render the template with the calculated cashback amount
    return render_template('payment_wallet_cashback.html', cashback_amount=cashback_amount)

@app.route('/recharge_balance', methods=['POST', 'GET'])
def recharge_balance():
    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Mobile number input
        amount = request.form['amount']          # Payment amount
        payment_method = request.form['payment_method']  # Payment method (cash/credit)

        try:
            # Validate input fields
            if not mobile_num or not amount or not payment_method:
                flash("All fields are required.", "danger")
                return render_template('recharge_balance.html')

            # Execute the stored procedure to recharge the balance
            query = text("""
                EXEC Initiate_balance_payment :mobile_num, :amount, :payment_method
            """)
            
            # Execute the query with the provided parameters
            db.session.execute(query, {
                'mobile_num': mobile_num,
                'amount': float(amount),  # Ensure it's treated as a float
                'payment_method': payment_method
            })
            
            # Commit the transaction
            db.session.commit()

            flash("Balance recharged successfully!", "success")
        except Exception as e:
            db.session.rollback()  # Rollback transaction on error
            flash(f"Error occurred while recharging balance: {str(e)}", "danger")
        
    return render_template('recharge_balance.html')

@app.route('/redeem_voucher', methods=['POST', 'GET'])
def redeem_voucher():
    if request.method == 'POST':
        mobile_num = request.form['mobile_num']  # Mobile number input
        voucher_id = request.form['voucher_id']  # Voucher ID input

        try:
            # Validate input fields
            if not mobile_num or not voucher_id:
                flash("Both fields are required.", "danger")
                return render_template('redeem_voucher.html')

            # Execute the stored procedure to redeem the voucher
            query = text("""
                EXEC Redeem_voucher_points :mobile_num, :voucher_id
            """)

            # Execute the query with the provided parameters
            db.session.execute(query, {
                'mobile_num': mobile_num,
                'voucher_id': int(voucher_id)  # Ensure it's treated as an integer
            })
            
            # Commit the transaction
            db.session.commit()

            flash("Voucher redeemed successfully!", "success")
        except Exception as e:
            db.session.rollback()  # Rollback transaction on error
            flash(f"Error occurred while redeeming voucher: {str(e)}", "danger")
        
    return render_template('redeem_voucher.html')

if __name__ == '__main__':
    app.run(debug=True)
