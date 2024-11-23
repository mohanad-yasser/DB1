from flask import Flask, render_template, flash, redirect, url_for, request

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

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
        # Placeholder for customer login logic
        flash("Customer login is not available at the moment.", "danger")

    return redirect(url_for('home'))

# View Customers route
@app.route('/view_customers')
def view_customers():
    return render_template('view_customers.html', customers=None)

# View Physical Stores
@app.route('/view_stores')
def view_stores():
    return render_template('view_stores.html', stores=None)

# View Resolved Tickets
@app.route('/view_resolved_tickets')
def view_resolved_tickets():
    return render_template('view_resolved_tickets.html', tickets=None)

# View Customer Accounts and Subscribed Plans
@app.route('/view_customer_accounts')
def view_customer_accounts():
    return render_template('view_customer_accounts.html', accounts=None)

# List Customer Accounts Subscribed to Input Plan ID on Input Date
@app.route('/list_accounts_by_plan', methods=['GET', 'POST'])
def list_accounts_by_plan():
    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        date = request.form.get('date')
        # Logic to fetch accounts based on plan_id and date will go here
        accounts = None  # Placeholder until DB integration
        return render_template('list_accounts_by_plan.html', accounts=accounts, plan_id=plan_id, date=date)
    return render_template('list_accounts_by_plan.html', accounts=None)

# Show Total Usage of Input Account on Each Subscribed Plan from Input Date
@app.route('/show_account_usage', methods=['GET', 'POST'])
def show_account_usage():
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        date = request.form.get('date')
        # Logic to fetch usage details based on account_id and date will go here
        usage = None  # Placeholder until DB integration
        return render_template('show_account_usage.html', usage=usage, account_id=account_id, date=date)
    return render_template('show_account_usage.html', usage=None)

# Remove Benefits from Input Account for a Certain Plan ID
@app.route('/remove_benefits', methods=['GET', 'POST'])
def remove_benefits():
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        plan_id = request.form.get('plan_id')
        # Logic to remove benefits will go here
        flash("Benefits removed successfully.", "success")
        return redirect(url_for('admin'))
    return render_template('remove_benefits.html')

# List All SMS Offers for a Certain Input Account
@app.route('/list_sms_offers', methods=['GET', 'POST'])
def list_sms_offers():
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        # Logic to fetch SMS offers based on account_id will go here
        sms_offers = None  # Placeholder until DB integration
        return render_template('list_sms_offers.html', sms_offers=sms_offers, account_id=account_id)
    return render_template('list_sms_offers.html', sms_offers=None)

if __name__ == '__main__':
    app.run(debug=True)
