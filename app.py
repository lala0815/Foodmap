from flask import Flask, render_template, request
from flask import redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import secrets
import pandas as pd
import uuid  
import os
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 生成一個隨機的密鑰

# 設置圖片儲存路徑
IMAGE_FOLDER = os.path.join(os.getcwd(), 'static', 'images')
# 設置 CSV 資料夾路徑
CSV_FOLDER = os.path.join(os.getcwd(), 'csv_files')

# 檢查資料夾是否存在
if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

# CSV 文件路徑
RESTAURANT_DATA_FILE = os.path.join(CSV_FOLDER, 'restaurants.csv')
REVIEWS_FILE = os.path.join(CSV_FOLDER, 'reviews.csv')
USER_DATA_FILE = os.path.join(CSV_FOLDER, 'users.csv')

def check_and_create_file(file_path, default_data):
    """檢查檔案是否存在，若不存在則創建並初始化資料"""
    if not os.path.exists(file_path):
        default_data.to_csv(file_path, index=False)

# 初始化 CSV 文件
check_and_create_file(USER_DATA_FILE, pd.DataFrame(columns=['username', 'password']))
check_and_create_file(REVIEWS_FILE, pd.DataFrame(columns=['restaurant_name', 'username', 'rating', 'comment']))
check_and_create_file(RESTAURANT_DATA_FILE, pd.DataFrame(columns=['name', 'type', 'latitude', 'longitude', 'address', 'phone', 'owner', 'rating', 'image', 'description']))

# 檢查圖片儲存資料夾是否存在，若不存在則創建
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def allowed_image(file):
    """檢查圖片格式是否被允許"""
    allowed_extensions = ['jpg', 'jpeg', 'png']
    file_extension = file.filename.split('.')[-1].lower()
    return file_extension in allowed_extensions

def convert_image_to_format(image, format='JPEG', max_retries=3):
    """將圖片轉換為指定格式，添加重試機制"""
    for attempt in range(max_retries):
        try:
            img = Image.open(image)
            img = img.convert('RGB')
            output = BytesIO()
            img.save(output, format=format)
            output.seek(0)
            return output
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f'圖片處理失敗：{str(e)}')
            continue

# 設定圖片檔案大小限制（例�� 5MB）
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            flash(f'發生錯誤：{str(e)}', 'error')
            return redirect(url_for('index'))
    return decorated_function

@app.route('/')
def index():
    logged_in = 'user' in session
    username = session.get('user') if logged_in else None
    return render_template('index.html', logged_in=logged_in, username=username)

def validate_restaurant_data(name, type, address, phone, latitude, longitude):
    errors = []
    
    if not all([name, type, address, phone]):
        errors.append('所有必填欄位都必須填寫')
        
    try:
        lat = float(latitude)
        lng = float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            errors.append('經緯度範圍不正確')
    except ValueError:
        errors.append('經緯度必須是有效的數字')
        
    # 驗證電話號碼格式
    if not re.match(r'^\+?[\d\s-]+$', phone):
        errors.append('電話號碼格式不正確')
        
    return errors

@app.route('/register-restaurant', methods=['GET', 'POST'])
@handle_errors
def register_restaurant():
    # 檢查用戶是否已登入
    if 'user' not in session:
        flash('請先登入後再註冊餐廳', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        # 獲取表單資料
        try:
            name = request.form.get('name').strip()
            type = request.form.get('type').strip()
            latitude_str = request.form.get('latitude').strip()
            longitude_str = request.form.get('longitude').strip()
            address = request.form.get('address').strip()
            phone = request.form.get('phone').strip()
            owner = request.form.get('owner').strip()
            description = request.form.get('description', '').strip()

            # 驗證經緯度格式
            if not latitude_str or not longitude_str:
                flash('Latitude and longitude are required.', 'error')
                return redirect(url_for('register_restaurant'))

            # 嘗試將經緯度轉換為浮點數
            try:
                latitude = float(latitude_str)
                longitude = float(longitude_str)
            except ValueError:
                flash('Invalid format for latitude or longitude. Please enter valid numbers.', 'error')
                return redirect(url_for('register_restaurant'))

            # 檢查經緯度範圍是否合理（以 WGS84 範圍為準）
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                flash('Latitude must be between -90 and 90, and longitude must be between -180 and 180.', 'error')
                return redirect(url_for('register_restaurant'))

        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'error')
            return redirect(url_for('register_restaurant'))

        # 處理圖片上傳
        images = request.files.getlist('images')
        image_filenames = []
        for image in images:
            if image.filename:
                # 檢查圖片格式
                if not allowed_image(image):
                    flash('Only JPG, JPEG, and PNG images are allowed.', 'error')
                    return redirect(url_for('register_restaurant'))

                # 檢查圖片檔案大小
                if image.content_length > MAX_IMAGE_SIZE:
                    flash('Image file is too large. Maximum size allowed is 5MB.', 'error')
                    return redirect(url_for('register_restaurant'))

                # 轉換圖片格式為 JPEG
                image_file = convert_image_to_format(image, format='JPEG')

                # 生成新的唯一文件名
                unique_filename = str(uuid.uuid4()) + '.jpg'
                converted_path = os.path.join(IMAGE_FOLDER, unique_filename)

                # 儲存轉換後的圖片
                with open(converted_path, 'wb') as f:
                    f.write(image_file.read())

                image_filenames.append(unique_filename)

        image_str = ','.join(image_filenames) if image_filenames else ''

        # 數據驗證：檢查必填欄位
        if not name or not type or not address or not phone:
            error_message = 'All required fields (excluding image and description) are mandatory！'
            return render_template('register-restaurant.html', error_message=error_message)

        # 讀取現有餐廳資料
        restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)

        # 檢查餐廳名稱是否完全相同
        duplicate_name = restaurant_df[restaurant_df['name'].str.lower() == name.lower()]

        # 檢查經緯度是否相近（重複位置檢查）
        is_latitude_close = abs(restaurant_df['latitude'].astype(float) - latitude) < 0.0001
        is_longitude_close = abs(restaurant_df['longitude'].astype(float) - longitude) < 0.0001
        duplicate_location = restaurant_df[is_latitude_close & is_longitude_close]

        # 如果名稱重複，返回錯誤
        if not duplicate_name.empty:
            flash(f"Registration failed! A restaurant with the same name '{name}' already exists at: Address: {duplicate_name.iloc[0]['address']}. Please choose a different name.", 'error')
            return redirect(url_for('register_restaurant'))

        # 如果位置重複，返回錯誤
        if not duplicate_location.empty:
            flash(f"Registration failed! This location is already registered by: Name: {duplicate_location.iloc[0]['name']}, Address: {duplicate_location.iloc[0]['address']}. Please confirm the location and try again.", 'error')
            return redirect(url_for('register_restaurant'))

        # 儲存餐廳資料至 CSV
        new_restaurant = pd.DataFrame({
            'name': [name],
            'type': [type],
            'latitude': [latitude],
            'longitude': [longitude],
            'address': [address],
            'phone': [phone],
            'owner': [owner],
            'rating': [0],
            'image': [image_str],
            'description': [description]
        })

        # 將新的餐廳資料儲存至 CSV
        restaurant_df = pd.concat([restaurant_df, new_restaurant], ignore_index=True)
        restaurant_df.to_csv(RESTAURANT_DATA_FILE, index=False)

        # 註冊成功後，跳轉到地圖頁面
        return redirect(url_for('map',
                                restaurant_name=name,
                                latitude=latitude,
                                longitude=longitude,
                                type=type,
                                address=address,
                                phone=phone,
                                rating=0,
                                owner=owner,
                                description=description))

    return render_template('register-restaurant.html')


@app.route('/map', methods=['GET', 'POST'])
def map():
    # 從最新的 restaurants.csv 讀取餐廳資料
    restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)

    # 只選取需要的欄位，並將資料轉換為字典格式
    restaurants = restaurant_df[['name', 'latitude', 'longitude', 'type', 'address', 'phone', 'owner', 'rating', 'image', 'description']].fillna('').to_dict(orient='records')

    # 預設經緯度為台北
    latitude = request.args.get('latitude', 25.0330, type=float)
    longitude = request.args.get('longitude', 121.5654, type=float)

    restaurant_name = request.args.get('restaurant_name', '')

    # 如果有搜尋餐廳名稱，過濾餐廳資料
    if restaurant_name:
        filtered_restaurants = [r for r in restaurants if restaurant_name.lower() in r['name'].lower()]
        if filtered_restaurants:
            # 如果找到符合條件的餐廳，將地圖聚焦在第一個餐廳位置
            first_restaurant = filtered_restaurants[0]
            latitude = first_restaurant['latitude']
            longitude = first_restaurant['longitude']
        else:
            flash('No matching restaurants found!', 'error')
            filtered_restaurants = []  # 沒有符合的餐廳
    else:
        filtered_restaurants = restaurants

    # 將資料傳遞給前端模板
    return render_template('map.html', restaurants=filtered_restaurants, latitude=latitude, longitude=longitude, restaurant_name=restaurant_name)



@app.route('/restaurant/<restaurant_name>', methods=['GET', 'POST'])
def restaurant_details(restaurant_name):
    restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)

    restaurant = restaurant_df[restaurant_df['name'] == restaurant_name].iloc[0]
    name = restaurant['name']
    type = restaurant['type']
    address = restaurant['address']
    phone = restaurant['phone']
    owner = restaurant['owner']
    rating = restaurant['rating']
    image = str(restaurant['image']) if pd.notna(restaurant['image']) else ''
    description = restaurant['description'] if pd.notna(restaurant['description']) else 'No description'

    reviews_df = pd.read_csv(REVIEWS_FILE)
    reviews = reviews_df[reviews_df['restaurant_name'] == restaurant_name].to_dict(orient='records')

    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login'))

        username = session['user']
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()

        # 如果評論是空白，將其設為 None
        if not comment:
            comment = "No comment"

        # 新增評論
        new_review = pd.DataFrame({
            'restaurant_name': [restaurant_name],
            'username': [username],
            'rating': [rating],
            'comment': [comment]
        })

        reviews_df = pd.concat([reviews_df, new_review], ignore_index=True)
        reviews_df.to_csv(REVIEWS_FILE, index=False)

        # 計算新的平均評分並四捨五入
        updated_rating = reviews_df[reviews_df['restaurant_name'] == restaurant_name]['rating'].mean()
        rounded_rating = round(updated_rating, 1)  # 四捨五入至小數點一位

        # 更新餐廳評分
        restaurant_df.loc[restaurant_df['name'] == restaurant_name, 'rating'] = rounded_rating
        restaurant_df.to_csv(RESTAURANT_DATA_FILE, index=False)

        # 顯示成功訊息
        flash('Your review has been submitted successfully!', 'success')

        return redirect(url_for('restaurant_details', restaurant_name=restaurant_name))

    #轉跳至地圖頁面並傳遞資訊
    return render_template(
        'restaurant_details.html',
        name=name,
        type=type,
        address=address,
        phone=phone,
        rating=rating,
        owner=owner,
        image=image,
        description=description,
        reviews=reviews
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password').strip()

        # 讀取用戶資料
        users = pd.read_csv(USER_DATA_FILE)
        # 清理用戶名與密碼
        users['username'] = users['username'].fillna('').astype(str).str.strip().str.lower()
        users['password'] = users['password'].fillna('').astype(str).str.strip()

        # 驗證用戶名和密碼
        if username in users['username'].values:
            stored_password = users.loc[users['username'] == username, 'password'].values[0]
            # 檢查密碼是否正確
            if check_password_hash(stored_password, password):
                session['user'] = username
                return redirect(url_for('index'))

        # 錯誤處理
        error_message = 'Login failed, please check your username or password.'
        return render_template('login.html', error_message=error_message)

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        # 檢查密碼複雜度
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$', password):
            error_message = '"Password must contain both uppercase and lowercase letters, as well as numbers, and be at least 6 characters long."'
            return render_template('register.html', error_message=error_message)
        
        # 檢查密碼和確認密碼是否匹配
        if password != confirm_password:
            error_message = 'The password and confirmation password do not match.'
            return render_template('register.html', error_message=error_message)

        # 讀取用戶資料
        users = pd.read_csv(USER_DATA_FILE)

        # 清理數據：將 username 欄位轉換為字串，處理空值
        users['username'] = users['username'].fillna('').astype(str).str.strip().str.lower()

        # 檢查用戶是否已存在
        if username in users['username'].values:
            error_message = 'The username is already taken.'
            return render_template('register.html', error_message=error_message)

        # 加密密碼
        hashed_password = generate_password_hash(password)

        # 新增用戶
        new_user = pd.DataFrame({'username': [username], 'password': [hashed_password]})
        users = pd.concat([users, new_user], ignore_index=True)

        # 儲存至 CSV
        users.to_csv(USER_DATA_FILE, index=False)

        # 註冊成功，顯示成功訊息並跳轉到登入頁面
        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)  # 清除會話
    return redirect(url_for('index'))

def safe_read_csv(file_path):
    """安全讀取 CSV 文件"""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        flash(f'讀取數據失敗：{str(e)}', 'error')
        return pd.DataFrame()

def safe_write_csv(df, file_path):
    """安全寫入 CSV 文件"""
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        flash(f'保存數據失敗：{str(e)}', 'error')
        return False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')