# 餐廳評論網站
這是一個使用 Flask 框架開發的餐廳評論網站，允許使用者註冊餐廳、查看地圖上的餐廳位置、發表評論和評分。
## 功能特點
- 使用者註冊和登入系統
 餐廳註冊功能（支援多張圖片上傳）
 地圖顯示所有餐廳位置
 餐廳搜尋功能
 餐廳評分和評論系統
 支援多圖片上傳和預覽
 整合地圖顯示功能
## 系統需求
- Python 3.7+
 Flask
 Pandas
 Pillow (PIL)
 Werkzeug
## 快速開始
1. **克隆專案**
```bash
git clone [repository-url]
cd restaurant-review-website
```
2. **安裝依賴**
```bash
pip install -r requirements.txt
```
3. **啟動應用**
```bash
python app.py
```
4. **訪問網站**
打開瀏覽器訪問 `http://localhost:5000`
## 目錄結構
```
restaurant-review-website/
├── app.py                 # 主應用程式
├── static/               # 靜態檔案
│   └── images/          # 圖片儲存目錄
├── templates/           # HTML 模板
│   ├── base.html        # 基礎模板
│   ├── index.html       # 首頁
│   ├── login.html       # 登入頁面
│   ├── register.html    # 註冊頁面
│   ├── register-restaurant.html  # 餐廳註冊頁面
│   ├── restaurant_details.html   # 餐廳詳情頁面
│   └── map.html         # 地圖頁面
├── csv_files/          # CSV 資料儲存
│   ├── restaurants.csv  # 餐廳資料
│   ├── reviews.csv     # 評論資料
│   └── users.csv       # 用戶資料
└── requirements.txt    # 專案依賴
```

## 使用說明

### 1. 用戶功能
- **註冊帳號**：點擊 "Sign Up" 創建新帳號
- **登入系統**：使用註冊的帳號和密碼登入
- **發表評論**：登入後可對餐廳進行評分和評論

### 2. 餐廳功能
- **註冊餐廳**：
  - 登入後點擊 "Register Restaurant"
  - 填寫餐廳資訊（名稱、類型、地址等）
  - 上傳餐廳圖片（支援多張）
  - 提供餐廳描述和關鍵字

- **瀏覽餐廳**：
  - 在地圖上查看所有餐廳位置
  - 點擊餐廳標記查看詳細資訊
  - 使用搜尋功能尋找特定餐廳

### 3. 評論系統
- 評分範圍：1-5 分
- 可以添加文字評論
- 評分會影響餐廳的整體評分

## 開發說明

### 資料儲存
- 使用 CSV 檔案儲存資料
- 圖片儲存在 static/images/ 目錄
- 自動創建必要的資料目錄

### 安全性
- 密碼使用 Werkzeug 進行加密
- 圖片上傳限制：
  - 僅允許 jpg、jpeg、png 格式
  - 檔案大小限制為 5MB
- 實作使用者驗證機制

## 注意事項

1. **檔案權限**
   - 確保 static/images/ 目錄可寫入
   - 確保 csv_files/ 目錄可寫入

2. **環境設置**
   - 建議使用虛擬環境
   - 確保所有依賴都已安裝

3. **資料備份**
   - 定期備份 CSV 檔案
   - 備份上傳的圖片

## 常見問題

1. **圖片上傳失敗**
   - 檢查檔案格式是否正確
   - 確認檔案大小是否超過限制
   - 驗證目錄權限

2. **評分顯示異常**
   - 確認評分輸入在 1-5 範圍內
   - 檢查 reviews.csv 檔案完整性

## 未來規劃

- [ ] 整合資料庫系統
- [ ] 添加管理員後台
- [ ] 優化圖片處理
- [ ] 增加社交功能
- [ ] 支援多語言

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交更改
4. 發送 Pull Request

## 授權

本專案採用 MIT 授權條款

## 聯絡方式

如有問題或建議，請聯繫：
[您的聯絡資訊]