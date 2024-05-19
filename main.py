# status_codes are not optional for the Redirect Response function. without it, the method will not run and will give
# an error output


from fastapi import FastAPI, HTTPException, Request, Form, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
from datetime import datetime
import pymysql.cursors

app = FastAPI()

templates = Jinja2Templates(directory="templates/")
logging.basicConfig(filename='app.log', level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

class AccountCreate(BaseModel):
    name: str
    acctype: str
    balance: int
    username: str
    password: str


connection = pymysql.connect(host='localhost',
                             user='aj',
                             password='abc',
                             database='practice',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            acctype VARCHAR(255) NOT NULL,
            balance INT NOT NULL,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)
    connection.commit()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                accnum VARCHAR(255) NOT NULL,
                transaction_date DATE NOT NULL,
                transaction_type VARCHAR(255) NOT NULL,
                amount FLOAT NOT NULL,
                new_balance FLOAT NOT NULL
            )
        """)
    connection.commit()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ############################################## CREATE ###############################################
@app.get("/renderCreateAccForm", response_class=HTMLResponse)
async def render_create_acc_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create", response_class=HTMLResponse)
async def create_account(
        request: Request,
        name: str = Form(...),
        acctype: str = Form(...),
        balance: int = Form(...),
        username: str = Form(...),
        password: str = Form(...)):
    with connection.cursor() as cursor:
        sql = "INSERT INTO accounts (name, acctype, balance,username, password) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (name, acctype, balance,username, password))
        connection.commit()
    return RedirectResponse(url="/account_created", status_code=303)



@app.get("/account_created", response_class=HTMLResponse)
async def account_created(request: Request):
    return templates.TemplateResponse("acc_created.html", {"request": request})

# ############################################## LOGIN ###############################################

# HELPER METHODS
async def start_session(response: Response, username: str):
    session_token = f"{username}:session"
    response.set_cookie(key="session_token", value=session_token)


@app.get("/renderLogin", response_class=HTMLResponse)
async def render_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login") # set cookie here and remove create acc from dashboard
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM accounts WHERE username = %s AND password = %s", (username,password))
            account = cursor.fetchone()
            logging.info('Here is acc: ' + str(account))
            if account is None:
                logging.info("Account is None")
                raise HTTPException(status_code=404, detail="Account not found") #check if acc exists
            else:
                logging.info("in else block")
                response = RedirectResponse(url="/postLogin", status_code=303)
                response.set_cookie(key='user', value=username)
                logging.info('cookie set')
                return response

    except:
        logging.info('came into exception')
        raise HTTPException(status_code=404, detail = 'code being annoying')
    #logging.info('right before return')
    #return {'message': username}
    #return RedirectResponse(url="/postLogin", status_code=303)

# if login (user pass combination) doesn't exist then return another page that has an error message with the same
# dashboard at the top, but this dashboard will still include the login page
# need to make edits to the other pages to remove the logins


# after login include dashboard -- copy and paste from all the other html files
@app.get('/postLogin', response_class = HTMLResponse)
async def new_login_page(request: Request):
    return templates.TemplateResponse("postLogin.html", {"request": request})
















# one more func for showing the output after login has been created

# ############################################## DEPOSIT ###############################################
@app.get("/renderDeposit", response_class=HTMLResponse)
async def render_deposit(request: Request):
    return templates.TemplateResponse("deposit.html", {"request": request})

def get_balance(cursor, accnum): # get rid of accnum
    sql = "SELECT balance FROM accounts WHERE id = %s"
    cursor.execute(sql, (accnum,))
    result = cursor.fetchone()
    if result:
        return result['balance']
    else:
        raise HTTPException(status_code=404, detail="Account not found")

@app.post("/deposit", response_class=HTMLResponse)
async def deposit(request: Request, accnum: int = Form(...), amt: int = Form(...)):
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE accounts SET balance = balance + %s WHERE id = %s"
            cursor.execute(sql, (amt, accnum))
            sql_insert_transaction = "INSERT INTO transaction_info (accnum, transaction_date, transaction_type, amount, new_balance) VALUES (%s, %s, %s, %s, %s)"
            transaction_date = datetime.today().strftime('%Y-%m-%d')
            new_balance = get_balance(cursor, accnum)
            cursor.execute(sql_insert_transaction, (accnum, transaction_date, "Deposit", amt, new_balance))
        connection.commit()
    except Exception as e:
        logging.error(f"Error depositing to account: {e}")
        raise HTTPException(status_code=500, detail="Could not deposit amount")
    return RedirectResponse(url="/depositCompleted", status_code=303)


@app.get("/depositCompleted",response_class=HTMLResponse)
async def depositComplete(request: Request):
    return templates.TemplateResponse("depositCompleted.html", {"request":request})

# ############################################## WITHDRAW ###############################################
@app.get("/renderWithdraw", response_class=HTMLResponse)
async def render_withdraw(request: Request):
    return templates.TemplateResponse("withdraw.html", {"request": request})

@app.post("/withdraw", response_class=HTMLResponse)
async def withdraw(request: Request, accnum: int = Form(...), amt: int = Form(...)):
    try:
        logging.info(f"Received withdrawal request for account number {accnum} and amount {amt}")
        with connection.cursor() as cursor:
            cursor.execute("SELECT balance FROM accounts WHERE id = %s", (accnum))
            account_balance_row = cursor.fetchone()
            logging.info(f"have fetchone {accnum}")
            logging.info(account_balance_row)
            if account_balance_row is None:
                logging.info("came into if block")
                raise HTTPException(status_code=404, detail="Account not found")
            account_balance = account_balance_row['balance']
            logging.info(f"Retrieved account balance for {accnum}: {account_balance}")
            logging.info(f"Withdrawing {amt} from account {accnum}")
            if amt > account_balance:
                raise HTTPException(status_code=406, detail="Withdrawal amount exceeds account balance")
            sql = "UPDATE accounts SET balance = balance - %s WHERE id = %s"
            cursor.execute(sql, (amt, accnum))
            sql_insert_transaction = "INSERT INTO transaction_info (accnum, transaction_date, transaction_type, amount, new_balance) VALUES (%s, %s, %s, %s, %s)"
            transaction_date = datetime.today().strftime('%Y-%m-%d')
            new_balance = get_balance(cursor, accnum)
            cursor.execute(sql_insert_transaction, (accnum, transaction_date, "Withdrawal", amt, new_balance))
        connection.commit()
        logging.info("Withdrawal successful")

    except Exception as e:
        logging.error(f"Error withdrawing from account: {e}")
        raise HTTPException(status_code=500, detail="Could not withdraw amount")

    return RedirectResponse(url="/withdrawCompleted", status_code=303)


@app.get("/withdrawCompleted",response_class=HTMLResponse)
async def withdrawComplete(request: Request):
    return templates.TemplateResponse("withdrawCompleted.html", {"request":request})



# ################ TRANSACTIONS ###############################

@app.get("/renderTransactions", response_class=HTMLResponse)
async def render_transactions(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})

@app.post("/transactions", response_class=HTMLResponse)
async def display_transactions(request: Request, accnum: int = Form(...)):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM transaction_info WHERE accnum = %s"
            cursor.execute(sql, (accnum,))
            transactions = cursor.fetchall()
            if not transactions:
                raise HTTPException(status_code=404, detail="No transactions found for the specified account")
    except Exception as e:
        logging.error(f"Error retrieving transactions: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve transactions")
    return templates.TemplateResponse("renderTransactions.html", {"request": request, "transactions": transactions})









# ################## INCOMPLETE INTEREST #############################
class InterestRequest(BaseModel):
    accnum: str
    date: str

@app.get("/renderInterest", response_class=HTMLResponse)
async def render_interest(request: Request):
    return templates.TemplateResponse("interest.html", {"request": request})

@app.post("/interest", response_class=HTMLResponse)
async def interest(request: Request, interest_req: InterestRequest):
    acc_num = interest_req.accnum
    later_date = interest_req.date
    today_str_obj = datetime.today().strftime('%Y-%m-%d')
    today_date_obj = datetime.strptime(today_str_obj, '%Y-%m-%d')
    later_date_obj = datetime.strptime(later_date, '%Y-%m-%d')
    delta = later_date_obj - today_date_obj

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM accounts WHERE id = %s"
            cursor.execute(sql, acc_num)
            acc_info = cursor.fetchone()

            if acc_info is None:
                raise HTTPException(status_code=404, detail="Account not found")

            principle = acc_info["starting_balance"]
            interest_amt = round(principle * pow((1.0001), delta.days), 2)

            # Update balance
            new_balance = acc_info["balance"] + interest_amt
            sql_update_balance = "UPDATE bank_acc_info SET balance = %s WHERE accnum = %s"
            cursor.execute(sql_update_balance, (new_balance, acc_num))

            # Record transaction
            sql_insert_transaction = "INSERT INTO transaction_info (accnum, transaction_date, transaction_type, amount, new_balance) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_insert_transaction, (acc_num, today_str_obj, "Interest", interest_amt, new_balance))

            connection.commit()

    except Exception as e:
        logging.error(f"Error processing interest: {e}")
        raise HTTPException(status_code=500, detail="Error processing interest")

    return templates.TemplateResponse("interestCompleted.html", {"request": request})

@app.get("/wit",response_class=HTMLResponse)
async def depositComplete(request: Request):
    return templates.TemplateResponse("withdrawCompleted.html", {"request":request})


# in all the other functions: transactions, deposit, withdrawal, they need to read the username from the cookie
# and use that to access the account details rather than the user inputting their own account number every time

# also make sure that we do a check on a username to make sure that its not already taken
