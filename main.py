from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
from datetime import datetime
import pymysql.cursors
from random import randint
app = FastAPI()

templates = Jinja2Templates(directory="templates/")
logging.basicConfig(filename='app.log', level=logging.DEBUG)


class AccountCreate(BaseModel):
    name: str
    acctype: str
    balance: int

class Transaction(BaseModel):
    accnum: int
    amt: int

class InterestCalc(BaseModel):
    accnum: int
    date: datetime


connection = pymysql.connect(host='localhost',
                             user='aj',
                             password='abc',
                             database='practice',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/renderCreateAccForm", response_class=HTMLResponse)
async def render_create_acc_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.get("/renderDeposit", response_class=HTMLResponse)
async def render_deposit(request: Request):
    return templates.TemplateResponse("deposit.html", {"request": request})

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




