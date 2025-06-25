from datetime import date, datetime, timedelta
from fastapi import FastAPI , Depends ,HTTPException, Query
from sqlmodel import Session, select
from enum import Enum
from sqlalchemy.orm import selectinload
from sqlalchemy import extract, func
from calendar import month_name
from weasyprint import HTML
from io import BytesIO
from fastapi.responses import StreamingResponse

#authentication
from auth import authenticate , create_access_token , get_current_user , hash_password , verify_hash_password , ACCESS_TOKEN_EXPIRY_MINUTES
from fastapi.security import OAuth2PasswordRequestForm

#models and schemas
from models import User , Category , Transaction , Savings
from schemas import UserCreate , UserRead , Token , CategoryCreate , CategoryRead , TransactionCreate , TransactionRead , categoryinfo , SavingsCreate , SavingsView , SavingsUpdate , SavingsTotal

#database
from database import get_session , create_db

class Tags(str , Enum):
    User = "User"
    Category = "Category"
    Transaction = "Transaction"
    Savings = "Savings"
    MonthlyReport = "Monthly Report"

app = FastAPI()

@app.on_event('startup')
def create_database_instance():
    create_db()

@app.post('/register' ,response_model= UserRead ,  tags=[Tags.User.value])
def register(user:UserCreate , session : Session = Depends(get_session)):
    new_password = hash_password(user.password)
    new_user = User(username=user.username , email=user.email , password=new_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post('/token' , response_model=Token , tags=[Tags.User.value])
def login(form_data : OAuth2PasswordRequestForm = Depends(), session:Session = Depends(get_session)):
    user = authenticate(form_data.username , form_data.password , session)
    if not user:
        raise HTTPException (status_code=401 , detail="User not found")
    access_token = create_access_token(data = {"sub":user.username},expiry_time=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES))
    return {"access_token":access_token ,"token_type":"bearer"}

#Category

@app.post("/category/add" ,response_model=CategoryRead , tags=[Tags.Category.value])
def add_category(category : CategoryCreate , session: Session = Depends(get_session), current_user : User = Depends(get_current_user)):
    new_category = Category(name=category.name , user_id=current_user.id)
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    return new_category

#Category List

@app.get("/category/all" ,response_model=list[CategoryRead] , tags=[Tags.Category.value])
def all_category(session: Session = Depends(get_session) , current_user :User = Depends(get_current_user)):
    user = current_user.id
    categories = session.exec(select(Category).where(Category.user_id == user)).all()
    return categories

#Category Delete

@app.delete("/category/delete/{category_id}", tags=[Tags.Category.value])
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    category = session.get(Category, category_id)

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session.delete(category)
    session.commit()
    return {"detail": "Deleted"}


#Transaction

@app.post("/transactions/add" , response_model=TransactionRead , tags=[Tags.Transaction.value])
def add_transactions(transactions : TransactionCreate , session:Session = Depends(get_session) , current_user : User = Depends(get_current_user)):
    new_transaction = Transaction(user_id=current_user.id ,title=transactions.title , amount= transactions.amount , type = transactions.type , category_id=transactions.category_id , optional_notes=transactions.optional_notes)
    session.add(new_transaction)
    session.commit()
    session.refresh(new_transaction)
    return new_transaction


#Transaction History

@app.get("/transactions/history" ,response_model=list[TransactionRead] , tags=[Tags.Transaction.value])
def all_transactions(session : Session = Depends(get_session) , current_user : User = Depends(get_current_user)):
    user = current_user.id
    transactions = session.exec(select(Transaction).where(Transaction.user_id ==user).options(selectinload(Transaction.category))).all()
    
    return [
        TransactionRead(
            id=i.id,
            title =i.title,
            amount=i.amount,
            type=i.type,
            category = categoryinfo(
                id = i.category.id,
                name= i.category.name
            )if i.category else None,
            date_added=i.date_added,
            optional_notes=i.optional_notes

        )
        for i in transactions
    ]

#Transaction Delete

@app.delete("/transactions/delete/{transaction_id}", tags=[Tags.Transaction.value])
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    transaction = session.get(Transaction, transaction_id)

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session.delete(transaction)
    session.commit()
    return {"detail": "Deleted"}

#Savings add
@app.post("/savings/add" , response_model=SavingsView , tags=[Tags.Savings.value])
def create_savings(savings:SavingsCreate , session:Session = Depends(get_session) , current_user: User = Depends(get_current_user)):
    user = current_user.id
    new_savings = Savings(user_id=user ,amount=savings.amount , optional_notes=savings.optional_notes )
    session.add(new_savings)
    session.commit()
    session.refresh(new_savings)
    return new_savings

#Savings history

@app.get("/savings/all" , response_model=list[SavingsView] , tags=[Tags.Savings.value])
def view_savings(session:Session = Depends(get_session) , current_user:User = Depends(get_current_user)):
    user = current_user.id
    savings_view = session.exec(select(Savings).where(Savings.user_id==user)).all()
    return savings_view

#Savings get 1

@app.get("/savings/get/{savings_id}" , response_model=SavingsView , tags=[Tags.Savings.value])
def view_savings_single(savings_id: int ,session:Session = Depends(get_session) , current_user: User = Depends(get_current_user)):
    user = current_user.i 
    savings_view = session.get(Savings,savings_id)
    return savings_view

#Savings Delete

@app.delete("/savings/delete/{savings_id}" , tags=[Tags.Savings.value])
def view_savings_single(savings_id: int ,session:Session = Depends(get_session) , current_user: User = Depends(get_current_user)):
    user = current_user.id
    savings = session.get(Savings , savings_id)

    if savings is None:
        raise HTTPException(status_code=404 , detail="Not Found")
    if savings.user_id!=user:
        raise HTTPException(status_code=403 , detail="Unauthorized")
    
    session.delete(savings)
    session.commit()
    return {"detail":"Deleted"}

#Savings update

@app.patch("/savings/update/{savings_id}" , response_model=SavingsCreate , tags=[Tags.Savings.value])
def update_savings(savings : SavingsUpdate , savings_id:int , session:Session = Depends(get_session) , current_user: User = Depends(get_current_user)):
    savings_db = session.get(Savings , savings_id)
    if savings_db is None:
        raise HTTPException(status_code=404 , detail="Not Found")
    savings_data = savings.model_dump(exclude_unset=True)
    savings_db.sqlmodel_update(savings_data)
    session.add(savings_db)
    session.commit()
    session.refresh(savings_db)
    return savings_db

#Savings Total

@app.get("/savings/totalamount" , tags=[Tags.Savings.value])
def totalSavingsamount(session:Session = Depends(get_session) , current_user : User = Depends(get_current_user)):
    user = current_user.id
    savings = session.exec(select(func.sum(Savings.amount)).where(Savings.user_id == user)).one() or 0
    return {"user" : current_user.username , "savings":savings}


#Monthly Report Endpoint

@app.get("/monthlyreport" , tags=[Tags.MonthlyReport.value])
def monthlyreport(month : int , session : Session = Depends(get_session) , current_user : User = Depends(get_current_user)):
    user = current_user.id

    statement = select(Transaction).where(Transaction.user_id == user ,extract("month" , Transaction.date_added) == month)
    
    transaction = session.exec(statement).all()
    savings = session.exec(select(func.sum(Savings.amount)).where(Savings.user_id == user)).one() or 0
    
    income = sum(i.amount for i in transaction if i.type == "income")
    expense = sum(i.amount for i in transaction if i.type == "expense")
    
    net = income -expense

    category_summary = {}
    for j in transaction:
        if j.type == "expense":
            category_name = j.category.name if j.category else "Uncategorized"
            category_summary[category_name] = category_summary.get(category_name , 0) + j.amount # category ko naam ra value same iteration ma hunxa , so default 0 garera jun iteration ma xa tei iteration ko amount add gatr

    return {
        "User":current_user.username,
        "Month" : month_name[month],
        "income": income,
        "expense":expense,
        "total-savings": savings,
        "Net transaction" : net,
        "Categories" : category_summary
    }

@app.get("/download/report" , tags=[Tags.MonthlyReport.value])
def Download_monthly_report(
    month : int , 
    session : Session = Depends(get_session),
    current_user : User = Depends(get_current_user)):

    user = current_user.id

    statement = select(Transaction).where(Transaction.user_id== user , extract("month" , Transaction.date_added)== month)

    transactions = session.exec(statement).all()

    #html content

    html_content = f"""
    <html>
    <head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 30px;
        }}
        h2 {{
            text-align: center;
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .summary {{
            margin-top: 30px;
            font-size: 1rem;
            font-weight: bold;
        }}
    </style>
    </head>
    <body>
    <h2>Monthly Report for {current_user.username} - Month {month}</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Category</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
    """

# Loop through transactions
    for t in transactions:
        category = t.category.name if t.category else "Uncategorized"
    html_content += f"""
        <tr>
            <td>{t.date_added}</td>
            <td>{t.type}</td>
            <td>{t.amount}</td>
            <td>{category}</td>
            <td>{t.optional_notes or ""}</td>
        </tr>
    """

# Close table and body
    html_content += """
        </tbody>
    </table>
    </body>
    </html>
    """

    pdf_io = BytesIO() #loads the file in memory
    HTML(string=html_content).write_pdf(pdf_io) # convert from html to pdf
    pdf_io.seek(0) # the pointer is at the last so reset the pointer to 0 for reading

    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition":f"attachment; filename=monthly_report_{month}{current_user.username}.pdf"} # these headers make the file downloadable instead of showing inline in browser
    )

