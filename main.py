from fastapi import FastAPI, HTTPException, Request, Form, Depends
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

# Establish MySQL connection
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
            balance INT NOT NULL
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
        user: AccountCreate = Depends()):
    with connection.cursor() as cursor:
        sql = "INSERT INTO accounts (name, acctype, balance) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user.name, user.acctype, user.balance))
        connection.commit()
    return RedirectResponse(url="/account_created", status_code=303)

@app.get("/account_created", response_class=HTMLResponse)
async def account_created(request: Request):
    return templates.TemplateResponse("acc_created.html", {"request": request})

# ############################################## DEPOSIT ###############################################
@app.get("/renderDeposit", response_class=HTMLResponse)
async def render_deposit(request: Request):
    return templates.TemplateResponse("deposit.html", {"request": request})

@app.post("/deposit", response_class=HTMLResponse)
async def deposit(request: Request, accnum: int = Form(...), amt: int = Form(...)):
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE accounts SET balance = balance + %s WHERE id = %s"
            cursor.execute(sql, (amt, accnum))
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
async def deposit(request: Request, accnum: int = Form(...), amt: int = Form(...)):
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
        connection.commit()
        logging.info("Withdrawal successful")

    except Exception as e:
        logging.error(f"Error withdrawing from account: {e}")
        raise HTTPException(status_code=500, detail="Could not withdraw amount")

    return RedirectResponse(url="/withdrawCompleted", status_code=303)


@app.get("/withdrawCompleted",response_class=HTMLResponse)
async def depositComplete(request: Request):
    return templates.TemplateResponse("withdrawCompleted.html", {"request":request})

'''

@app.get("/renderWithdraw", response_class=HTMLResponse)
async def render_withdraw(request: Request):
    return templates.TemplateResponse("withdraw.html", {"request": request})

@app.get("/renderInterest", response_class=HTMLResponse)
async def render_interest(request: Request):
    return templates.TemplateResponse("interest.html", {"request": request})

@app.get("/renderTransactions", response_class=HTMLResponse)
async def render_transactions(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})


@app.post("/create",response_class=HTMLResponse)
def create_account(account: AccountCreate, request: Request):
    try:
        acc_num = randint(0, 10000)
        with connection.cursor() as cursor:
            sql = "INSERT INTO accounts (acc_num, name, account_type, balance, starting_balance) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (acc_num, account.name, account.acctype, account.balance, account.balance))
        connection.commit()
    except Exception as e:
        logging.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail="Could not create account")
    return templates.TemplateResponse("acc_created.html", {"request": request})

@app.post("/deposit")
def deposit(transaction: Transaction):
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE accounts SET balance = balance + %s WHERE acc_num = %s"
            cursor.execute(sql, (transaction.amt, transaction.accnum))
        connection.commit()
    except Exception as e:
        logging.error(f"Error depositing to account: {e}")
        raise HTTPException(status_code=500, detail="Could not deposit amount")

@app.post("/withdraw")
def withdraw(transaction: Transaction):
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE accounts SET balance = balance - %s WHERE acc_num = %s"
            cursor.execute(sql, (transaction.amt, transaction.accnum))
        connection.commit()
    except Exception as e:
        logging.error(f"Error withdrawing from account: {e}")
        raise HTTPException(status_code=500, detail="Could not withdraw amount")

'''












'''
######
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccountCreate(BaseModel):
    name: str
    acc_type: str
    balance: int

class Transaction(BaseModel):
    accnum: int
    amt: int

connection = pymysql.connect(host='localhost',
                             user='aj',
                             password='abc',
                             database='practice',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/create", response_class=HTMLResponse)
async def render_create_acc(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create", response_class=HTMLResponse)
async def create_account(account: AccountCreate):
    try:
        # insert into database
        with connection.cursor() as cursor:
            sql = "INSERT INTO accounts (name, acc_type, balance, starting_balance) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (account.name, account.acc_type, account.balance, account.balance))
        #connection.commit()
    except:
        pass
    return templates.TemplateResponse("acc_created.html")

@app.get("/deposit", response_class=HTMLResponse)
async def render_deposit(request: Request):
    return templates.TemplateResponse("deposit.html", {"request": request})



@app.get("/withdraw", response_class=HTMLResponse)
async def render_withdraw(request: Request):
    return templates.TemplateResponse("withdraw.html", {"request": request})
'''


'''
@app.post("/interest")
def calculate_interest(interest_data: InterestCalc):
    return {"message": "Interest calculated successfully"}

@app.post("/transactions")
def view_transactions(request: Request):
    acc_num = request.form["accnum"]
    return {"message": "Transactions retrieved successfully"}
'''



'''
@app.post("/create", response_class=HTMLResponse)
async def create_account(
        request: Request,
        name: str = Form(...),
        acctype: str = Form(...),
        balance: int = Form(...)):
    with connection.cursor() as cursor:
        sql = "INSERT INTO accounts (name, acctype, balance) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, acctype, balance))
        connection.commit()
    return RedirectResponse(url="/account_created", status_code=303)
'''
