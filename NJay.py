

import hashlib
import mysql.connector
import random
from flask import Flask, render_template, url_for,request,session,redirect,jsonify
from flask_mail import Mail,Message
from numpy import double
from config import mail_username,mail_password
import os
from flask_session import Session

app = Flask(__name__)
connection=mysql.connector.connect(
    host="localhost",
    database="njayybank",
    port="3306",
    user="root",
    password=""
    
)
cursor=connection.cursor()
app.secret_key='secret'
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = mail_username
app.config['MAIL_PASSWORD'] = mail_password
# app.config["SESSION_PERMANENT"] = False
# Session(app)


cursor=connection.cursor(buffered=True)
app.secret_key='secret'
mail=Mail(app)

def generateAccountNumber():
    return random.randrange(1111111111,9999999999)
@app.route('/' ,methods=['POST','GET'])
def index():
    msg='User Not logged in Login Please Login'
    return render_template('login.html')

@app.route('/home')
def home():
    
        accountNumber=session['accountno']
        statement=cursor.execute("SELECT * FROM transactionstable WHERE sendersAccountNumber=%s OR recieversAccountnumber=%s",(accountNumber,accountNumber))
        statement = cursor.fetchall();
        amountDeposited=cursor.execute("SELECT amount FROM transactionstable WHERE ttype='Deposit'AND sendersAccountNumber=%s",(session.get('accountno'),))
        amountDeposited=cursor.fetchall()   
        finalAmount=0
        for x in amountDeposited:
            finalAmount+=double(x)
        
        amountWithdrawn=cursor.execute("SELECT amount FROM transactionstable WHERE ttype='Withdraw'AND sendersAccountNumber=%s",(session.get('accountno'),))
        amountWithdrawn=cursor.fetchall()   
        finalAmountW=0
        for x in amountWithdrawn:
            finalAmountW+=double(x)
            
        amountTransferred=cursor.execute("SELECT amount FROM transactionstable WHERE ttype='Transfer'AND sendersAccountNumber=%s",(session.get('accountno'),))
        amountTransferred=cursor.fetchall()   
        finalAmountT=0
        for x in amountTransferred:
            finalAmountT+=double(x)
            
        
        return render_template("index.html",firstname=session['firstname'],lastname=session["lastname"],balance=session['totalBalance'],allstatement=statement,finalAmount=int(finalAmount),finalAmountT=int(finalAmountT),finalAmountW=int(finalAmountW))

@app.route('/login',methods=["POST","GET"])
def login():
    if request.method=='GET':

        return render_template('login.html')
    else:
        msg=''
        accountnumber=request.form.get("accountnumber",False)
        password=request.form.get("password")
        rows=cursor.execute("SELECT * FROM users WHERE accountnumber=%s AND passwords=%s",(accountnumber,password))
        rows=cursor.fetchone()
        connection.commit()
    
        if rows:
            session['loggedin']=True
            session['accountno']=rows[1]
            session['firstname']=rows[2]
            session['lastname']=rows[3]
            session['passwords']=rows[5]
            
            session['totalBalance']=rows[6]
            
            return redirect(url_for('home'))
        else:
           msg='Incorrect Account Number/Password'
           return render_template('login.html',msg=msg) 
        
        
    
@app.route('/register',methods=["POST","GET"])
def register():
    if request.method=="GET":
        return render_template("login.html")
    else:
        first_name=request.form["fn"]
        last_name=request.form["ln"]
        email=request.form["email"]
        password=request.form["password"]
        accountNumber=str(random.randrange(1111111111,9999999999))
        balance=0
        cursor.execute('SELECT email FROM users WHERE email=%s',(email,))
        user=cursor.fetchall()
        if user:
            msg='Email Address ALREADY EXIST'
            return render_template('login.html',msg=msg)
        else:
            
            query2="INSERT INTO users(accountnumber,firstname,lastname,email,passwords,balance)VALUES(%s,%s,%s,%s,%s,%s)"
            val=(accountNumber,first_name,last_name,email,password,balance)
            cursor.execute(query2,val)
            connection.commit()
            msg=Message(subject=f"Mail to {first_name} {last_name}",sender=mail_username,recipients=[email])
            msg.body=f"Welcome to Bank NJAY \n This is your account Number:{accountNumber}"
            mail.send(msg)
            session['accountno']=accountNumber
            session['email']=email
            print(accountNumber)
            return render_template("login.html",success=True)
            
@app.route("/deposit",methods=["GET",'POST'])
def deposit():
    if request.method=="GET":
        if not 'accountno' in session:
            msg ='User not logged in please login in '
            return render_template('login.html',msg=msg)
        else:
            return render_template("deposit.html",firstname=session['firstname'],lastname=session["lastname"],)
    else:
        
        if "accountno" in session:
            amount=request.form['amount']
            amount=int(amount)
            password=request.form['pin']
            totalBalance=0
            cursor.execute('SELECT balance FROM users WHERE accountnumber=%s AND passwords=%s',(session.get('accountno'),password))
            balance=cursor.fetchone()
            if balance:
                balance=int(balance[0])
                totalBalance=balance+amount
                cursor.execute(f"UPDATE users SET balance=%s WHERE passwords=%s",(totalBalance,password))
                
                connection.commit()
                accountNumber=session.get('accountno')
                ttype='Deposit'
                cursor.execute('INSERT INTO transactionstable (sendersAccountNumber,ttype,amount)VALUES(%s,%s,%s)',(accountNumber,ttype,amount))
                connection.commit()
                session['totalBalance']=totalBalance
                return redirect(url_for('home'))
            else:
                msg='Wrong Password Try again'
            return render_template('deposit.html',msg=msg)
        else:
            msg='PLEASE LOGIN'
            return redirect(url_for('login'))
       
        
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('accountno', None)
   session.pop('firstname', None)
   session.pop('lastname', None)
   session.pop('balance', None)
   return redirect(url_for('login'))
            
            
        
@app.route("/withdraw",methods=["GET",'POST'])
def withdraw():
    if request.method=="GET":
        if not 'accountno' in session:
            msg ='User not logged in please login in '
            return render_template('login.html',msg=msg)
        return render_template("withdrawal.html",firstname=session['firstname'],lastname=session["lastname"],)
    else:
        if 'accountno' in session:
            amount=request.form['amount']
            password=request.form['pin']
            accountNumber=session.get('accountno')
            cursor.execute('SELECT balance FROM users WHERE accountnumber=%s AND passwords=%s',(accountNumber,password))
            balance=cursor.fetchone()
            if balance:
                balance=int(balance[0])
                if int(amount)>balance:
                    msg='INSUFFIENT FUNDS'
                    return render_template('withdrawal.html',msg=msg)
                else:
                    totalBalance=balance-int(amount)
                    cursor.execute(f"UPDATE users SET balance={totalBalance} WHERE accountnumber=%s AND passwords=%s",(accountNumber,password))
                    
                    connection.commit()
                    ttype='Withdraw'
                    cursor.execute('INSERT INTO transactionstable (sendersAccountNumber,ttype,amount) VALUES(%s,%s,%s)',(accountNumber,ttype,amount))
                    connection.commit()
                    session['totalBalance']=totalBalance
                    return redirect(url_for('home'))     
            else:
                msg='Wrong Password Try again'
            return render_template('withdrawal.html',msg=msg)   

@app.route("/transfer",methods=["GET",'POST'])
def transfer():
    if request.method=="GET":
        if not 'accountno' in session:
            msg ='User not logged in please login in'
            return render_template('login.html',msg=msg)
        return render_template("transfer.html",firstname=session['firstname'],lastname=session["lastname"],)
    else:
        if 'accountno' in session:
            recieversaccountNumber=request.form['accountnumber']
            
            sendersaccountnumber=session.get('accountno')
            amount=request.form['amount']
            amount=int(amount)
            password=request.form['pin']
            
            cursor.execute('SELECT balance FROM users WHERE accountnumber=%s AND passwords=%s',(sendersaccountnumber,password))
            sbalance=cursor.fetchone()
            if sbalance:
                sbalance=int(sbalance[0])
                if int(amount)>sbalance:
                    msg='INSUFFIENT FUNDS'
                    return render_template('transfer.html',msg=msg)
                else:
                    cursor.execute('SELECT balance FROM users WHERE accountnumber=%s',(recieversaccountNumber,))
                    rbalance=cursor.fetchone()
                    if rbalance:
                        rbalance=int(rbalance[0])
                        rbalance+=amount
                        totalBalance=sbalance-int(amount)
                        cursor.execute(f"UPDATE users SET balance={totalBalance} WHERE accountnumber=%s AND passwords=%s",(sendersaccountnumber,password))
                        cursor.execute(f"UPDATE users SET balance={rbalance} WHERE accountnumber=%s ",(recieversaccountNumber,))
                        
                        connection.commit()
                        ttype='Transfer'
                        cursor.execute('INSERT INTO transactionstable (sendersAccountNumber,ttype,amount) VALUES(%s,%s,%s)',(sendersaccountnumber,ttype,amount))
                        connection.commit()
                        ttyper='Recieved'
                        cursor.execute('INSERT INTO transactionstable (recieversAccountnumber,ttype,amount) VALUES(%s,%s,%s)',(recieversaccountNumber,ttyper,amount))
                        connection.commit()
                        session['totalBalance']=totalBalance
                        
                        return redirect(url_for('home'))      
                    else:
                        msg='Recipient AccountNumber does not exist'
                        return render_template('transfer.html',msg=msg)
            else:
                msg='Wrong Password Try again'
                return render_template('transfer.html',msg=msg)      


    
   
        

if __name__ == '__main__':
    app.run(debug = True)