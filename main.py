from flask import Flask,request,jsonify,send_file,make_response
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token, get_jwt
import mysql.connector
from datetime import timedelta
from mysql.connector import Error
from flask_socketio import SocketIO
from camera import VideoCamera
import os
from flask_cors import CORS
import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from datetime import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JWT_SECRET_KEY'] = 'GFPT'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
jwt = JWTManager(app)
CORS(app)  # เปิดใช้งาน CORS
socketio = SocketIO(app, cors_allowed_origins="*")
camera = VideoCamera()
blacklist = set()

# host='192.168.2.130'
# user='test'
# password='test'
# database='cornai'


host='localhost:3300'
user='root'
password='1234'
database='CornAI'

######################################################################
#API base
@app.route('/')
def index():
    return ""
######################################################################


######################################################################

#######DELETE TOKEN
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in blacklist


@app.route('/api/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    blacklist.add(str(jti))  # แปลง jti เป็น string ก่อนเพิ่มเข้าไปใน blacklist
    return jsonify({"msg": "Successfully logged out"}), 200
######################################################################

######################################################################
# API Product
#ดึงproductทั้งหมด
@app.route('/api/products' ,methods=['GET'])
@jwt_required()
def products():
    try:
        # Connect to the database
        mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
        mycursor = mydb.cursor(dictionary=True)
        
        # Get current user from JWT
        current_user = get_jwt_identity()
        
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        
        # Fetch products if user exists
        mycursor.execute("SELECT * FROM products")
        myresult = mycursor.fetchall()
        
        # Close the database connection
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": str(e)}), 500)
    
    return make_response(jsonify(myresult), 200)

#ดึงproductตามid
@app.route('/api/products/<id>' ,methods=['GET'])
@jwt_required()
def products_id_losts(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = "SELECT * FROM products  WHERE products.id = %s;"
        val = (f"{id}",)
        mycursor.execute(sql,val)
        result = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(result),200)

#insert product
@app.route('/api/products', methods=['POST'])
@jwt_required()
def products_insert():
    try:
        mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
        data = request.get_json()
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        print(user_result['id'])
        sql = """INSERT INTO products (id_lots, id_user, BreakClean, CompleteSeeds, Dust, MoldSpores, broken, fullbrokenseeds, path)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (
             data['id'],user_result['id'], data['BreakClean'], data['CompleteSeeds'], data['Dust'],
            data['MoldSpores'], data['broken'], data['fullbrokenseeds'], data['path']
        )
        mycursor.execute(sql, val)
        mydb.commit()
        mycursor.close()
        mydb.close()
        return make_response(jsonify({"rowcount": mycursor.rowcount}), 200)
    except Error as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return make_response(jsonify({"msg": error_msg}), 500)

#update product
@app.route('/api/products', methods=['PUT'])
@jwt_required()
def products_update():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        data = request.get_json()
        mycursor = mydb.cursor(dictionary=True)
        sql = "UPDATE `products` SET `id_lots`=%s WHERE products.id = %s;"
        val = (data['id_lots'],data['id'])
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

#delete product
@app.route('/api/products/<id>', methods=['DELETE'])
@jwt_required()
def products_delete(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        data = request.get_json()
        filename = data['file']
        print(filename)
        sql = "DELETE FROM `products` WHERE products.id = %s;"
        os.remove(filename)
        val = (f"{id}",)
        mycursor.execute(sql, val)  
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"file": filename}),200)
@app.route('/api/graphproduct/<id>', methods=['GET'])
@jwt_required()
def lots_productgraphID(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
         # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        val =(f"{id}",)
        sql = """
            SELECT p.id,
            ROUND((p.BreakClean/(p.BreakClean+p.CompleteSeeds+p.Dust+p.MoldSpores+p.broken+p.fullbrokenseeds))*100,2) as BreakClean,
            ROUND((p.CompleteSeeds/(p.BreakClean+p.CompleteSeeds+p.Dust+p.MoldSpores+p.broken+p.fullbrokenseeds))*100,2) as CompleteSeeds,
            ROUND((p.Dust/(p.BreakClean+p.CompleteSeeds+p.Dust+p.MoldSpores+p.broken+p.fullbrokenseeds))*100,2) as Dust,
            ROUND((p.MoldSpores/(p.BreakClean+p.CompleteSeeds+p.Dust+p.MoldSpores+p.broken+p.fullbrokenseeds))*100,2) as MoldSpores,
            ROUND((p.broken/(p.BreakClean+p.CompleteSeeds+p.Dust+p.MoldSpores+p.broken+p.fullbrokenseeds))*100,2) as broken,
            ROUND((p.fullbrokenseeds/(p.BreakClean+p.CompleteSeeds+p.Dust+p.MoldSpores+p.broken+p.fullbrokenseeds))*100,2) as fullbrokenseeds,
            SUM(p.BreakClean)as CountBreakClean,SUM(p.CompleteSeeds)as CountCompleteSeeds,
            SUM(p.Dust)as CountDust,SUM(p.MoldSpores)as CountMoldSpores,SUM(p.broken)as Countbroken,
            SUM(p.fullbrokenseeds)as Countfullbrokenseeds
            FROM `products` as p
            WHERE p.id = %s;
            """
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify(myresult),200)
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
######################################################################



######################################################################
# API Lots

#ดึงข้อมูลเป็นหน้าๆ
@app.route('/api/lots/<page>', methods=['GET'])
@jwt_required()
def lots_page(page):
    try:
        page_value = int(page)
        max_value = 8
        min_value = (page_value-1)*8
        print(max_value)
        print(min_value)
        if max_value is None or min_value is None:
            return make_response(jsonify({"msg": "Missing 'max' or 'min' in request"}), 400)

        query = """
            SELECT lots.id as id,lots.name as lots,lots.date as date,t2.path as path , s.status as status
            FROM lots INNER JOIN (SELECT p.id_lots AS max_id, p.path FROM products AS p
            JOIN (SELECT MAX(id) AS id, id_lots FROM products GROUP BY id_lots) AS p_max 
            ON p.id = p_max.id AND p.id_lots = p_max.id_lots) as t2
			on t2.max_id = lots.id 
            left JOIN (SELECT status.id_lots as id,status.status as status FROM status INNER JOIN 
            (SELECT max(status.id) as id FROM status GROUP BY status.id_lots) 
            as smax on smax.id = status.id)as s ON lots.id = s.id
           	ORDER BY lots.id DESC
            LIMIT %s OFFSET %s;
        """
        values = (max_value, min_value)
        with mysql.connector.connect(host=host, user=user, password=password, database=database) as mydb:
            with mydb.cursor(dictionary=True) as mycursor:
                # Get current user from JWT
                current_user = get_jwt_identity()
                # Check if the user exists
                sql = "SELECT * FROM user WHERE name = %s"
                val = (current_user,)
                mycursor.execute(sql, val)
                user_result = mycursor.fetchone()
                # If user does not exist, return an error response
                if not user_result:
                    return make_response(jsonify({"msg": "Token is bad"}), 404)
                mycursor.execute(query, values)
                myresult = mycursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": str(e)}), 500)
    return make_response(jsonify(myresult), 200)
 

#ดึงจำนวนหน้า
@app.route('/api/lots/sum',methods=['GET'])
@jwt_required()
def lots_sum():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = """SELECT COUNT(lots.id) as sum
            FROM lots INNER JOIN (SELECT p.id_lots AS max_id, p.path FROM products AS p
            JOIN (SELECT MAX(id) AS id, id_lots FROM products GROUP BY id_lots) AS p_max 
            ON p.id = p_max.id AND p.id_lots = p_max.id_lots) as t2
			on t2.max_id = lots.id;"""
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        count = myresult[0]['sum']
        sum = count//8
        if(count%8 != 0):
            sum += 1
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"sum":sum}),200)

#ดึงจำนวนหน้าที่ค้นหา
@app.route('/api/lots/search/sum',methods=['POST'])
@jwt_required()
def lots_like_sum():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        data = request.get_json()
        id = data.get('id')
        sql = """SELECT COUNT(lots.id) as sum
            FROM lots INNER JOIN (SELECT p.id_lots AS max_id, p.path FROM products AS p
            JOIN (SELECT MAX(id) AS id, id_lots FROM products GROUP BY id_lots) AS p_max 
            ON p.id = p_max.id AND p.id_lots = p_max.id_lots) as t2
			on t2.max_id = lots.id
            WHERE lots.name LIKE %s;"""
        val = (f"%{id}%",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        count = myresult[0]['sum']
        sum = count//8
        if(count%8 != 0):
            sum += 1
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"sum":sum}),200)

#ดึงหน้าที่ค้นหา
@app.route('/api/lots/search',methods=['POST'])
@jwt_required()
def lots_like_id():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        data = request.get_json()
        page = data.get('page')
        id = data.get('id')
        page_value = int(page)
        max_value = 8 
        min_value = (page_value-1)*8
        sql = ("""
            SELECT lots.id as id,lots.name as lots,lots.date as date,t2.path as path , s.status as status
            FROM lots INNER JOIN (SELECT p.id_lots AS max_id, p.path FROM products AS p
            JOIN (SELECT MAX(id) AS id, id_lots FROM products GROUP BY id_lots) AS p_max 
            ON p.id = p_max.id AND p.id_lots = p_max.id_lots) as t2
			on t2.max_id = lots.id 
            left JOIN (SELECT status.id_lots as id,status.status as status FROM status INNER JOIN 
            (SELECT max(status.id) as id FROM status GROUP BY status.id_lots) 
            as smax on smax.id = status.id)as s ON lots.id = s.id
            WHERE lots.name LIKE %s
           	ORDER BY lots.id DESC 
            LIMIT %s OFFSET %s;
        """)
        val = ("%"+id+"%",max_value,min_value) 
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)

#ดึงล็อตตามid
@app.route('/api/lotId/<id>', methods=['GET'])
@jwt_required()
def lots_id(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = ("""SELECT * FROM lots 
                INNER JOIN products ON products.id_lots = lots.id
                WHERE lots.id = %s;""")
        val = (f"{id}",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)

#ดึงล็อตตามid
@app.route('/api/lotstatusId/<id>', methods=['GET'])
@jwt_required()
def lots_idstatus(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = ("""SELECT * FROM lots LEFT JOIN
                (SELECT status.id_lots as id,status.status as status FROM status INNER JOIN 
                (SELECT max(status.id) as id FROM status GROUP BY status.id_lots) 
                as smax on smax.id = status.id) as st ON lots.id = st.id
                WHERE lots.id = %s;""")
        val = (f"{id}",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)


#ดึงล็อตทั้งหมด
@app.route('/api/lots', methods=['GET'])
@jwt_required()
def lots():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        
        sql = "SELECT * FROM lots;"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify(myresult),200)
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)

#สร้างล็อต
@app.route('/api/lots', methods=['POST'])
@jwt_required()
def lots_insert():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        data = request.get_json()
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d")
        name = data['name']
        sql = ("INSERT INTO `lots`(`name`, `date`) VALUES (%s,%s);")
        val = (name,current_time)
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

###update
@app.route('/api/lots', methods=['PUT'])
@jwt_required()
def lots_update():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        data = request.get_json()
        name = data['name']
        id = data['id']
        sql = ("UPDATE `lots` SET `name` =%s  WHERE lots.id = %s ")
        val = (name,id)
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)


#ลบล็อต
@app.route('/api/lots/<id>', methods=['DELETE'])
@jwt_required()
def lots_delete(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = ("DELETE FROM lots WHERE lots.id = %s;")
        val =(f"{id}",)
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

#ดึงล็อตกราฟทั้งหมด
@app.route('/api/graph/<id>', methods=['GET'])
@jwt_required()
def lots_productgraph(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        val =(f"{id}",)
        sql = """SELECT ROUND((SUM(p.BreakClean)/ (SUM(p.BreakClean)+SUM(p.CompleteSeeds)+SUM(p.Dust)+SUM(p.MoldSpores)+SUM(p.broken)+SUM(p.fullbrokenseeds)))*100,2) as BreakClean,
            ROUND((SUM(p.CompleteSeeds)/ (SUM(p.BreakClean)+SUM(p.CompleteSeeds)+SUM(p.Dust)+SUM(p.MoldSpores)+SUM(p.broken)+SUM(p.fullbrokenseeds)))*100,2) as CompleteSeeds,
            ROUND((SUM(p.Dust)/ 
            (SUM(p.BreakClean)+SUM(p.CompleteSeeds)+SUM(p.Dust)+SUM(p.MoldSpores)+SUM(p.broken)+SUM(p.fullbrokenseeds)))*100,2) as 
            Dust,
            ROUND((SUM(p.MoldSpores)/ 
            (SUM(p.BreakClean)+SUM(p.CompleteSeeds)+SUM(p.Dust)+SUM(p.MoldSpores)+SUM(p.broken)+SUM(p.fullbrokenseeds)))*100,2) as
            MoldSpores,
            ROUND((SUM(p.broken)/ 
            (SUM(p.BreakClean)+SUM(p.CompleteSeeds)+SUM(p.Dust)+SUM(p.MoldSpores)+SUM(p.broken)+SUM(p.fullbrokenseeds)))*100,2) as
            broken,
            ROUND((SUM(p.fullbrokenseeds)/ (SUM(p.BreakClean)+SUM(p.CompleteSeeds)+SUM(p.Dust)+SUM(p.MoldSpores)+SUM(p.broken)+SUM(p.fullbrokenseeds)))*100,2) as
            fullbrokenseeds,
            (p.BreakClean)as CountBreakClean,SUM(p.CompleteSeeds)as CountCompleteSeeds,
            SUM(p.Dust)as CountDust,SUM(p.MoldSpores)as CountMoldSpores,SUM(p.broken)as Countbroken,
            SUM(p.fullbrokenseeds)as Countfullbrokenseeds

            FROM lots as l 
            INNER JOIN products as p ON p.id_lots = l.id
            WHERE l.id = %s
            GROUP by p.id_lots;;"""
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify(myresult),200)
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    
######################################################################

######################################################################
# API Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data:
        usernameuser = data['username']
        passworduser = data['password']
        mydb = None
        mycursor = None
        try:
            # เปิดการเชื่อมต่อกับฐานข้อมูล
            mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
            mycursor = mydb.cursor(dictionary=True)
            #ใช้คำสั่ง SQL พร้อมกับการป้องกัน SQL Injection โดยใช้พารามิเตอร์
            sql = "SELECT * FROM user WHERE name = %s AND password = %s"
            mycursor.execute(sql, (usernameuser, passworduser))
            #ตรวจสอบผลลัพธ์ที่ได้จากฐานข้อมูล
            user_record = mycursor.fetchone()
            if user_record:
                access_token = create_access_token(identity=usernameuser)
                return make_response(jsonify({"Role": user_record['Role'],"Token":access_token}),200)
            else:
                return make_response(jsonify({"msg": "not found user or password"}),401)
        except Error as e:
                print(f"Error: {e}")
                return make_response("Internal Server Error", 500)
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()
######################################################################


######################################################################
#API Status
#get status
@app.route('/api/status/<id>',methods=['GET'])
@jwt_required()
def status_id(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = "SELECT * FROM status WHERE status.id_lots = %s ORDER BY status.id DESC LIMIT 1;"
        val = (f"{id}",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)

#insert status
@app.route('/api/status',methods=['POST'])
@jwt_required()
def status_insert():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT user.id FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        print(user_result['id'])
        id = user_result['id']
        data = request.get_json()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        
        sql = """INSERT INTO `status`(`id_lots`, `id_user`, `status`, `date`) VALUES 
        (%s,%s,%s,%s)"""
        val = (data['idlot'],id,data['status'],data['date'])
        mycursor.execute(sql,val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)





@app.route('/api/status',methods=['GET'])
@jwt_required()
def status():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = """SELECT user.name as name ,lots.name as lots ,s.status as status,s.date as date 
        FROM status as s INNER JOIN lots on s.id_lots = lots.id
        INNER JOIN user on user.id = s.id_user;"""
        mycursor.execute(sql,)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify({"myresult": myresult}),200)
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    
#เอาไว้ค้นหาตาม
@app.route('/api/status/search',methods=['POST'])
@jwt_required()
def statusSearch():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        # Get current user from JWT
        current_user = get_jwt_identity()
        # Check if the user exists
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        # If user does not exist, return an error response
        if not user_result:
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        sql = """SELECT user.name as name ,lots.name as lots ,s.status as status,s.date as date 
        FROM status as s INNER JOIN lots on s.id_lots = lots.id
        INNER JOIN user on user.id = s.id_user
        WHERE lots.name LIKE %s ;"""
        data = request.get_json()
        name = data.get('name')
        val = ("%"+name+"%",) 
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify({"myresult": myresult}),200)
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    
######################################################################
#api user
#get all
@app.route('/api/user',methods=['GET'])
@jwt_required()
def user_get():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        current_user = get_jwt_identity()
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        if(user_result['Role'] != "admin"):
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        query = """SELECT * FROM `user` WHERE 1;"""
        mycursor.execute(query,)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify({"myresult": myresult}),200)
    except Error as e:
        return make_response(jsonify({"msg": e}),500)
#get id
@app.route('/api/user/<id>',methods=['GET'])
@jwt_required()
def user_id(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        current_user = get_jwt_identity()
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        if(user_result['Role'] != "admin"):
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        query = """SELECT * FROM `user` WHERE user.id = %s;"""
        val = (id,)
        mycursor.execute(query,val)
        myresult = mycursor.fetchone()
        mydb.close()
        return make_response(jsonify({"myresult": myresult}),200)
    except Error as e:
        return make_response(jsonify({"msg": e}),500)
#post 
@app.route('/api/user',methods=['POST'])
@jwt_required()
def user_insert():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        current_user = get_jwt_identity()
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        if(user_result['Role'] != "admin"):
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        query = """INSERT INTO `user`(`name`, `password`, `Role`) VALUES (%s,%s,%s);"""
        data = request.get_json()
        val = (data['name'],data['password'],data['Role'])
        mycursor.execute(query,val)
        mydb.commit()
        mydb.close()
        return make_response(jsonify({"rowcount": mycursor.rowcount}),200)
    except Error as e:
        return make_response(jsonify({"msg": e}),500)
    
#put
@app.route('/api/user',methods=['PUT'])
@jwt_required()
def user_update():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        current_user = get_jwt_identity()
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        if(user_result['Role'] != "admin"):
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        query = """UPDATE user SET `name`=%s,`password`=%s,`Role`=%s WHERE user.id = %s;"""
        data = request.get_json()
        val = (data['name'],data['password'],data['Role'],data['id'])
        mycursor.execute(query,val)
        mydb.commit()
        mydb.close()
        return make_response(jsonify({"rowcount": mycursor.rowcount}),200)
    except Error as e:
        return make_response(jsonify({"msg": e}),500)
#delete
@app.route('/api/user',methods=['DELETE'])
@jwt_required()
def user_delete():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        current_user = get_jwt_identity()
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        if(user_result['Role'] != "admin"):
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        query = """DELETE FROM user WHERE user.id = %s;"""
        data = request.get_json()
        val = (data['id'],)
        mycursor.execute(query,val)
        mydb.commit()
        mydb.close()
        return make_response(jsonify({"rowcount": mycursor.rowcount}),200)
    except Error as e:
        return make_response(jsonify({"msg": e}),500)
    
#get id
@app.route('/api/user/search',methods=['POST'])
@jwt_required()
def user_search():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        current_user = get_jwt_identity()
        sql = "SELECT * FROM user WHERE name = %s"
        val = (current_user,)
        mycursor.execute(sql, val)
        user_result = mycursor.fetchone()
        if(user_result['Role'] != "admin"):
            return make_response(jsonify({"msg": "Token is bad"}), 404)
        query = """SELECT * FROM `user` WHERE user.name LIKE %s;"""
        data = request.get_json()
        id = data.get('id')
        val1 = ("%"+id+"%",)
        mycursor.execute(query,val1)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify({"myresult": myresult}),200)
    except Error as e:
        return make_response(jsonify({"msg": e}),500)
######################################################################
# API detection
# ส่งรูปจากกล้องมา
@app.route('/request_pic', methods=['POST'])
@jwt_required()
def handle_request_video():
    # Connect to the database
    mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
    mycursor = mydb.cursor(dictionary=True)
        
    # Get current user from JWT
    current_user = get_jwt_identity()
        
    # Check if the user exists
    sql = "SELECT * FROM user WHERE name = %s"
    val = (current_user,)
    mycursor.execute(sql, val)
    user_result = mycursor.fetchone()
        
    # If user does not exist, return an error response
    if not user_result:
        return make_response(jsonify({"msg": "Token is bad"}), 404)
    # แปลง base64 กลับมาเป็นภาพ
    data = request.get_json()
    datas = data['imageData']
    header, encoded = datas.split(",", 1)
    img_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(img_data))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    if frame is not None:
        frames, num,filename = camera.get_pic(frame)
        print(num)
        sum = num[0]+num[1]+num[2]+num[3]+num[4]#+num[5]
        false = num[1]
        if(sum != 0):
            
            percent = (false/sum) *100
            x = float("{:.2f}".format(percent))
            # print(x)
        else:
            x = 0
        response_data = {
        "num": num,      # ข้อมูลตัวเลข
        "filename": filename,  # ชื่อไฟล์
        "percent": x
        
        }
        if frames is not None: 
            print(num)
            return jsonify(response_data)
        else:   
            return "Error: Failed to grab frame from camera"
    else :
        print("ssss")

# ลบรูปที่ถ่าย
@app.route('/delete_capture', methods=['POST'])
@jwt_required()
def delete_capture():
    # Connect to the database
    mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
    mycursor = mydb.cursor(dictionary=True)
        
    # Get current user from JWT
    current_user = get_jwt_identity()
        
    # Check if the user exists
    sql = "SELECT * FROM user WHERE name = %s"
    val = (current_user,)
    mycursor.execute(sql, val)
    user_result = mycursor.fetchone()
        
    # If user does not exist, return an error response
    if not user_result:
        return make_response(jsonify({"msg": "Token is bad"}), 404)
    data = request.get_json()
    filename = data['filename']
    if os.path.exists(filename):
        os.remove(filename)
        return jsonify({'status': 'Delete', 'data_received': data}), 200
    else:
        return jsonify({'error': 'No data provided'}), 400

# ส่งVideoกลับไป
@socketio.on('frame')
def handle_frame(data):
    # แปลง base64 กลับมาเป็นภาพ
    header, encoded = data.split(",", 1)
    img_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(img_data))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    # ทำการประมวลผลภาพ เช่น แสดงภาพ
    if frame is not None:
        frames, num = camera.get_test(frame)
        if frames is not None: 
            # ส่งข้อมูลเฟรมและตัวเลข num ผ่าน Socket.IO ไปยังเว็บไซต์
            print(num)
            sum = num[0]+num[1]+num[2]+num[3]+num[4]#+num[5]
            false = num[1]
            if(sum != 0):
                percent = (false/sum) *100
                x = float("{:.2f}".format(percent))
                # print(x)
            else:
                x = 0
            socketio.emit('response', {'frame':frames, 'num': num,'percent':x})
        else:
            return "Error: Failed to grab frame from camera"

# ดึงรูปที่ถ่าย
@app.route('/image', methods=['GET'])
def image():
    filename = request.args.get('filename')
    print("aaaaa=" + filename)
    file_path = os.path.join(app.root_path, filename) 
    if os.path.exists(file_path):  # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        return send_file(file_path, mimetype='image/jpeg')
    else:
        return "File not found", 404  # ส่งโค้ด 404 หากไม่พบไฟล์
######################################################################



######################################################################
# Main
if __name__ == '__main__':
    app.run()
######################################################################