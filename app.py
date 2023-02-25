import os
from bson import json_util
from flask import Flask,  request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from mongo import insertDocument, readDocuments, appendDoc, checkifexists
import json
from twilio.rest import Client

app = Flask(__name__)
db = SQLAlchemy()
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("Database_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://iem_examination_portal_user:MXGyw8N4NETYDvaSGKJk1ePOggi2kYWK@dpg-cfsvlvha6gdotccdnpt0-a.singapore-postgres.render.com/iem_examination_portal"
db.init_app(app)

#####============================ AMAZON S3 BUCKET CONFIFURATION=================================================####

# S3_BUCKET = "my-bucket-name"
# S3_KEY = "AWS_ACCESS_KEY_ID"
# S3_SECRET = "AWS_SECRET_ACCESS_KEY"
# S3_LOCATION = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)

#####============================ AMAZON S3 BUCKET CONFIFURATION=================================================####

####======================================TWILIO INTEGRATION====================================================####

account_sid = "ACe2ba56170748bc7babe48fb27243d56f"
auth_token = "351a3b3f0bd03dc61f6ad528d15aad7a"
verify_sid = "VA2e90c9ad693e9d95fecc64153fac2ddd"


@app.route("/smsotpPhone", methods=["GET", "POST"])
def otp_create():
    if request.method == 'POST':
        verified_number=request.json['phonenumber']
        client = Client(account_sid, auth_token)

        verification = client.verify.v2.services(verify_sid) \
          .verifications \
          .create(to=verified_number, channel="sms")
        print(verification.status)

@app.route("/smsotpver/<path:verified_number>", methods=["GET", "POST"])
def otp_check(verified_number):
    if request.method == 'POST':
        otp_code=request.json['otpcode']
        client = Client(account_sid, auth_token)
        verification_check = client.verify.v2.services(verify_sid) \
          .verification_checks \
          .create(to=verified_number, code=otp_code)
        ans= (verification_check.status)
        print(ans)
        return jsonify({"verification_status":ans})


####======================================TWILIO INTEGRATION ENDS====================================================####

class Students(db.Model):
    enrollment_number = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    phone_number = db.Column(db.String, unique=True, nullable=False)

class Exams(db.Model):
    examid= db.Column(db.Integer, primary_key= True)
    exam_name = db.Column(db.String, nullable= False)
    exam_startDate= db.Column(db.String, nullable = False)
    exam_startTime = db.Column(db.String, nullable=False)
    semester= db.Column(db.Integer, nullable= False)
    ## 2022-03-21 19:04:14
    exam_duration = db.Column(db.Integer, nullable = False)
    subject_code= db.Column(db.String, nullable = False)
    session= db.Column(db.String, nullable = False)

class Teacher(db.Model):
    teacherid= db.Column(db.String, nullable = False, primary_key=True)
    name= db.Column(db.String, nullable= False)
    phoneNumber= db.Column(db.String, nullable = False)
    email= db.Column(db.String, nullable = False)

with app.app_context():
    db.create_all()
    db.session.commit()

####=====================================DATABASE ENDS HERE=========================================================================####


####==================================STUDENT SECTION STARTS==========================================================================####
@app.route("/signup", methods=["GET", "POST"])
def user_create():
    if request.method == 'POST':
        enrollment_number = request.json['enrollment_number']
        name = request.json['name']
        email = request.json['email']
        phone_number = request.json['phone_number']
        users = Students(enrollment_number=enrollment_number, name=name, email=email, phone_number=phone_number)
        with app.app_context():
            db.session.add(users)
            db.session.commit()
        j=jsonify({"enrollment_number":enrollment_number, "name":name, "email":email, "phone":phone_number})
        dict= {"enrollment_number":enrollment_number, "name":name, "email":email, "phone":phone_number}
        insertDocument(dict)
        return jsonify({"auth":True})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        enrollment_number = request.json['enrollment_number']
        phone_number = request.json['phone_number']
        with app.app_context():
            enrol=Students.query.filter_by(phone_number=phone_number).first()
            phone=Students.query.filter_by(enrollment_number=enrollment_number).first()
            if(enrol==phone):
                auth=True
            else:
                auth=False
    return jsonify({"auth":auth})

####===========================STUDENT SECTION ENDS========================================================================================####

#####===========================UPLOADING IMG TO AWS BUCKET=======================================#####

# @app.route('/uploadimg', methods=['POST'])
# def upload_file():
#     file = request.files['file']
#     s3 = boto3.client(
#         "s3",
#         aws_access_key_id=S3_KEY,
#         aws_secret_access_key=S3_SECRET
#     )
#     s3.upload_fileobj(
#         file,
#         S3_BUCKET,
#         file.filename,
#         ExtraArgs={
#             "ContentType": file.content_type
#         }
#     )
#
#     return "{}{}".format(S3_LOCATION, file.filename)

#####===========================UPLOADING IMG TO AWS BUCKET ENDS=======================================#####


@app.route("/marks/<int:enrollment_number>", methods=["POST", "GET"])
def marksadd(enrollment_number):
    if request.method=="POST":
        enrollment=request.json['enrollment']
        marks=request.json['marks']
        examid=request.json["examid"]
        flag=checkifexists(examid,enrollment)
        if(flag==True):
            appendDoc(marks, int(examid), str(enrollment_number))
        return None


@app.route("/createTest", methods=["POST", "GET"])
def create_test():
    if request.method=="POST":
        ExamName=request.json['ExamName']
        SubjectCode= request.json['SubjectCode']
        Session= request.json['Session']
        Date= request.json['Date']
        Starttime= request.json['StartTime']
        semester= request.json['semester']
        duration= request.json['duration']
        # examstartDate= datetime.strptime(Date, "%Y-%m-%d")
        # StartTime= datetime.strptime(Starttime, "%H:%M")
        exams= Exams(exam_name=ExamName, subject_code=SubjectCode, exam_startDate= Date, exam_startTime=Starttime, exam_duration= duration, session= Session, semester=semester)

        with app.app_context():
            db.session.add(exams)
            db.session.commit()
        with app.app_context():
            q2 = Exams.query.filter_by(exam_name=ExamName).first()
            print(type(q2.examid))
            print(q2)
            id=q2.examid
            strid= str(id)
            todays= date.today()
            finalid= "IEM@"+ str(todays.year) + strid
        return jsonify({'examid': finalid})



# @app.route("/startcheck", methods=["POST","GET"])
# def startcheck():
#     if request.method=="POST":
#         starttest=False
#         examid= request.json['examid']
#         with app.app_context():
#             time= f"select exam_startTime from Exams where examid={examid}"
#             date= f"select exam_startDate from Exams where examid={examid}"
#             dur= f"select exam_duration from Exams where examid={examid}"
#         nw=datetime.now()
#         currdate=nw.date()
#         currtime= nw.time()
#         if(currdate== date):
#             if(time>currtime):
#                 starttest=True
#         if(starttest==True):
#             return jsonify({"examid": examid})

@app.route('/addQ', methods=['POST','GET'])
def questions():
    if request.method=='POST':
        questionList = request.json['ExamPaper']
        insertDocument(questionList)
        return jsonify({'trigger':True})




@app.route('/teachersignup', methods=["POST", "GET"])
def teachersignup():
    if request.method=="POST":
        teacherid=request.json["teacherid"]
        phoneNumber=request.json["phoneNumber"]
        email=request.json["email"]
        name= request.json['name']
        addT=Teacher(teacherid=teacherid, phoneNumber=phoneNumber, email=email, name=name)
        with app.app_context():
            db.session.add(addT)
            db.session.commit()
        return  jsonify({'teachername': name, 'auth':True})

@app.route('/teacherlogin', methods=["POST","GET"])
def teacherlogin():
    if request.method=="POST":
        teacherid=request.json["teacherid"]
        phoneNumber=request.json["phoneNumber"]
        with app.app_context():
            q0=f"select phoneNumber from Teacher where teacherid={teacherid}"
            q=db.engine.execute(q0)
            for i in q:
                q1=i[0]
            if(phoneNumber==q1):
                auth=True
            else:
                auth=False
            q9=f"select name from Teacher where teacherid={teacherid}"
            q21=db.engine.execute(q9)
            for i in q21:
                q2=i[0]
        return jsonify({'teachername': q2, "auth": auth})

@app.route('/entercode', methods=["POST", "GET"])
def enterexamcode():
    if request.method=="POST":
        examcode= request.json['examCode']
        enrollment= request.json['enrollment_number']
        code= examcode[4:]
        examCode= int(code)
        qpaper= readDocuments(int(examCode))
        qp=parse_json(qpaper)
        with app.app_context():
            q12=f"select exam_duration from Exams where examid={examCode}"
            q13= f"select exam_startTime from Exams where examid={examCode}"
            q14= f"select exam_startDate from Exams where examid={examCode}"
            q01=db.engine.execute(q12)
            q02 = db.engine.execute(q13)
            q03 = db.engine.execute(q14)
            l=[]
            for i in q01:
                q2=i[0]
                l.append(int(q2))
            for i in q02:
                q3=i[0]
                l.append(q3)
            for i in q03:
                q4=i[0]
                l.append(q4)
        dur= q2*60*1000
        nw = datetime.now()
        currdate=nw.strftime("%Y-%m-%d")
        currtime= nw.strftime("%H:%M:%S")
        if(q4==currdate):
            diff= datetime.strptime(q3, "%H:%M:%S")-datetime.strptime(currtime, "%H:%M:%S")
            ms = diff.total_seconds() * 1000
        else:
            datediff= datetime.strptime(q4, "%Y-%m-%d")- datetime.strptime(currdate, "%Y-%m-%d")
            diff = datetime.strptime(q3, "%H:%M:%S")-datetime.strptime(currtime, "%H:%M:%S")
            totaldiff= datediff*24*60*60 +diff
            ms = totaldiff.total_seconds() * 1000

        currtime0 = nw.strftime("%H:%M:%S")
        currtime1 = datetime.strptime(currtime0, "%H:%M:%S")
        extime= datetime.strptime(q3, "%H:%M:%S")
        if(extime>=currtime1):
            flag="Positive"
        else:
            flag="Negative"
        examchecker= checkifexists(examCode, enrollment)

        return jsonify({"questionpaper": qp, "remainingTime": ms, "duration": dur, "difference": flag,  "eligibility": examchecker})

@app.route('/markslenden', methods=["POST","GET"])
def marksexchanger():
    if request.method=="POST":
        marks= request.json['marks']
    return jsonify({"marks": marks})

def parse_json(data):
    return json.loads(json_util.dumps(data))


# with app.app_context():
#     ExamName= "Midsem 1 Digital Electronics"
#     q1 = f"select examid from Exams where exam_name= {ExamName}"
#     q2 = Exams.query.filter_by(exam_name=ExamName).first()
#     print(type(q2))
#     print(q2)
#     print(q2.examid)
# nw= datetime.now()
# currdate=nw.date()
# currtime=nw.strftime("%Y-%m-%d")
# print(currdate)
# print(currtime)
# print(type(currtime))

# with app.app_context():
#     tim= "9:00:30"
#     nw= datetime.now()
#     currtime = nw.strftime("%H:%M:%S")
#     currtime1=datetime.strptime(currtime, "%H:%M:%S")
#     tim1= datetime.strptime(tim, "%H:%M:%S")
#     if(tim1>currtime1):
#         print("YES")
#     else:
#         print("NO")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/student/login')
def sLogin():
    return render_template('index.html')

@app.route('/teacher/login')
def tLogin():
    return render_template('index.html')

@app.route('/student')
def s():
    return render_template('index.html')

@app.route('/teacher')
def t():
    return render_template('index.html')

@app.route('/teacher/<int:examid>/addQuestion')
def qadd(examid):
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)