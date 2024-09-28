# status_codes are not optional for the Redirect Response function. without it, the method will not run and will give
# an error output

from fastapi import FastAPI, HTTPException, Request, Form, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
from datetime import datetime
import pymysql.cursors
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates/")
# original
# logging.basicConfig(filename='app.log', level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')


# ensures that logging will work across all machines 
log_file_path = 'logs/app.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info('Application started')

class AccountCreate(BaseModel):
    name: str
    acctype: str
    balance: int
    username: str
    password: str
#'''
host = os.getenv("HOST")
user = os.getenv("USER")
pw = os.getenv("PASSWORD")
db= os.getenv("DATABASE")
connection = pymysql.connect(host=host,
                             user=user,
                             password=pw,
                             database=db,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
#'''



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
            #logging.info('Here is acc: ' + str(account))
            logger.info('Here is acc: ' + str(account))
            if account is None:
                logging.info("Account is None")
                raise HTTPException(status_code=404, detail="Account not found") #check if acc exists
            else:
                #logging.info("in else block")
                logger.info("in else block")
                response = RedirectResponse(url="/postLogin", status_code=303)
                response.set_cookie(key='user', value=username)
                logging.info('cookie set')
                return response

    except:
        #logging.info('came into exception')
        logger.info('came into exception')
        raise HTTPException(status_code=404, detail = 'code being annoying')

# if login (user pass combination) doesn't exist then return another page that has an error message with the same
# dashboard at the top, but this dashboard will still include the login page
# need to make edits to the other pages to remove the logins


# after login include dashboard -- copy and paste from all the other html files
@app.get('/postLogin', response_class = HTMLResponse)
async def new_login_page(request: Request):
    return templates.TemplateResponse("postLogin.html", {"request": request})



# ############################################## LOGOUT ###############################################

@app.get('/renderLogout', response_class=HTMLResponse)
async def renderLogout(request: Request):
    return templates.TemplateResponse("logout.html",{"request": request})

@app.post("/logout")
async def logout(response: Response):
    #logging.info("in logout")
    logger.info("in logout")
    response = RedirectResponse(url="/postLogout", status_code=303) # if we want to set or delete a cookie, we need to
    # do it as a RedirectResponse object. we can't just take response as an input to the logout function, it needs to be
    # redefined inside the actual function itself
    #logging.info("redirected url")
    logger.info("redirected url")
    response.delete_cookie("user")
    #logging.info("deleted cookie")
    logger.info('deleted cookie')
    return response
    #response.delete_cookie("user")
    #logging.info("logged out")
    #return RedirectResponse(url='/postLogout', status_code=303)

@app.get("/postLogout", response_class=HTMLResponse)
async def index_page(request: Request):
    #logging.info("in post logout function -- rendering index.html ")
    logger.info("in post logout function -- rendering index.html ")
    return templates.TemplateResponse("index.html", {"request": request})





# ############################################## DEPOSIT ###############################################
@app.get("/renderDeposit", response_class=HTMLResponse)
async def render_deposit(request: Request):
    return templates.TemplateResponse("deposit.html", {"request": request})


def get_balance(cursor, username):
    sql = "SELECT balance FROM accounts WHERE username = %s"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()
    #logging.info(f"here is the result for get balance: {result}")
    logger.info(f"here is the result for get balance: {result}")
    if result:
        return result['balance']
    else:
        raise HTTPException(status_code=404, detail="Account not found")


@app.post("/deposit", response_class=HTMLResponse)
async def deposit(request: Request, amt: int = Form(...)):
    # find condition for when cookie is not set
    try:
        with connection.cursor() as cursor:
            username = request.cookies.get("user")
            logging.info(username)
            sql = "SELECT balance FROM accounts WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            #logging.info(result)
            logger.info(result)
            sql = "UPDATE accounts SET balance = balance + %s WHERE username = %s"
            cursor.execute(sql, (amt, username))

            cursor.execute("SELECT id FROM accounts WHERE username = %s", (username,))
            acc_details = cursor.fetchone()
            #logging.info(f"Here are the acc_details: {acc_details}")
            logger.info(f"Here are the acc_details: {acc_details}")
            account_number = acc_details['id']

            sql_insert_transaction = "INSERT INTO transaction_info (accnum, transaction_date, transaction_type, amount, new_balance) VALUES (%s, %s, %s, %s, %s)"
            transaction_date = datetime.today().strftime('%Y-%m-%d')
            new_balance = get_balance(cursor, username)
            cursor.execute(sql_insert_transaction, (account_number, transaction_date, "Deposit", amt, new_balance))

        connection.commit()
    except Exception as e:
        #logging.error(f"Error depositing to account: {e}")
        logger.error(f"Error depositing to account: {e}")
        #raise HTTPException(status_code=500, detail="Could not deposit amount")
        return RedirectResponse(url="/renderLogin", status_code=303)


    return RedirectResponse(url="/depositCompleted", status_code=303)


@app.get("/depositCompleted",response_class=HTMLResponse)
async def depositComplete(request: Request):
    return templates.TemplateResponse("depositCompleted.html", {"request":request})







# ############################################## WITHDRAW ###############################################
@app.get("/renderWithdraw", response_class=HTMLResponse)
async def render_withdraw(request: Request):
    return templates.TemplateResponse("withdraw.html", {"request": request})



@app.post("/withdraw", response_class=HTMLResponse)
async def withdraw(request: Request, amt: int = Form(...)):
    try:
        username = request.cookies.get('user')
        #logging.info(f'username = {username}')
        logger.info(f'username = {username}')
        with connection.cursor() as cursor:
            cursor.execute("SELECT balance FROM accounts WHERE username = %s", (username,))
            user_details = cursor.fetchone()
            #logging.info(user_details)
            logger.info(user_details)
            if user_details is None:
                #logging.info("came into if block")
                logger.info("came into if block")
                raise HTTPException(status_code=404, detail="Account not found")

            account_balance = user_details['balance']
            #logging.info(f"Retrieved account balance for {username}: {account_balance}")
            logger.info(f"Retrieved account balance for {username}: {account_balance}")
            # logging.info(f"Withdrawing {amt} from account {accnum}")
            if amt > account_balance:
                raise HTTPException(status_code=406, detail="Withdrawal amount exceeds account balance")
            #logging.info("before SQL")
            logger.info("before SQL")
            sql = "UPDATE accounts SET balance = balance - %s WHERE username = %s"
            cursor.execute(sql, (amt, username))
            connection.commit()
            #logging.info("after SQL")
            logger.info("after SQL")

            cursor.execute("SELECT id FROM accounts WHERE username = %s", (username,))
            acc_id = cursor.fetchone()
            #logging.info(f"Here are the acc_details: {acc_id}")
            logger.info(f"Here are the acc_details: {acc_id}")
            account_number = acc_id['id']
            #logging.info(f"Have account number: {account_number}")
            logger.info(f"Have account number: {account_number}")

            sql_insert_transaction = "INSERT INTO transaction_info (accnum, transaction_date, transaction_type, amount, new_balance) VALUES (%s, %s, %s, %s, %s)"
            #logging.info("after second sql")
            logger.info("after second sql")
            transaction_date = datetime.today().strftime('%Y-%m-%d')
            #logging.info("after trans date")
            logger.info("after trans date")

            sql_id = "SELECT balance FROM accounts WHERE id=%s"
            cursor.execute(sql_id, account_number)
            user_details = cursor.fetchone()
            new_balance = user_details['balance']
            #logging.info("after new balance")
            #logging.info(f"new balance is {new_balance}")
            logger.info(f"new balance is {new_balance}")
            cursor.execute(sql_insert_transaction, (account_number, transaction_date, "Withdrawal", amt, new_balance))
            connection.commit()

        connection.commit()
        #logging.info("Withdrawal successful")
        logger.info("Withdrawal successful")

    except Exception as e:
        #logging.error(f"Error withdrawing from account: {e}")
        logger.error(f"Error withdrawing from account: {e}")
        return RedirectResponse(url="/renderLogin", status_code=303)
        #raise HTTPException(status_code=500, detail="Could not withdraw amount")

    return RedirectResponse(url="/withdrawCompleted", status_code=303)


@app.get("/withdrawCompleted",response_class=HTMLResponse)
async def withdrawComplete(request: Request):
    return templates.TemplateResponse("withdrawCompleted.html", {"request":request})



# ################ TRANSACTIONS ###############################

@app.get("/renderTransactions", response_class=HTMLResponse)
async def render_transactions(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})

@app.post("/transactions", response_class=HTMLResponse)
async def display_transactions(request: Request):
    try:
        username = request.cookies.get('user')
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM accounts WHERE username = %s", (username,))
            acc_details = cursor.fetchone()
            #logging.info(f"Here are the acc_details: {acc_details}")
            logger.info(f"Here are the acc_details: {acc_details}")
            account_number = acc_details['id']

            sql = "SELECT * FROM transaction_info WHERE accnum = %s"
            cursor.execute(sql, (account_number,))
            transactions = cursor.fetchall()
            if not transactions:
                raise HTTPException(status_code=404, detail="No transactions found for the specified account")
    except Exception as e:
        #logging.error(f"Error retrieving transactions: {e}")
        logger.error(f"Error retrieving transactions: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve transactions")
    return templates.TemplateResponse("renderTransactions.html", {"request": request, "transactions": transactions})









# ################## INTEREST #############################
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



