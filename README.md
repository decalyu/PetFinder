# 宠物寻找系统

使用AI图像识别技术帮助用户找到与上传图片相似的宠物。

## 功能概述

- 用户上传宠物图片
- 系统使用ResNet101模型识别并寻找相似宠物
- 显示匹配结果和宠物主人联系信息

## 技术栈

- **后端**: Flask, PyTorch, ResNet101
- **前端**: React

## 项目结构

```
petcode/
  ├── backend/           # Flask API服务
  │   ├── app.py         # Flask应用入口
  │   ├── model.py       # 图像识别模型
  │   ├── database/      # 宠物图片数据库
  │   └── uploads/       # 用户上传图片目录
  ├── frontend/          # React前端应用
  │   ├── src/           # 源代码
  │   │   ├── App.js     # 主应用组件
  │   │   └── App.css    # 样式表
  │   └── public/        # 静态资源
  └── README.md          # 项目文档
```

## 安装与运行

### 后端设置

1. 进入后端目录：
   ```
   cd backend
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 运行Flask服务器：
   ```
   python app.py
   ```
   服务器将在 http://localhost:5000 运行

### 前端设置

1. 进入前端目录：
   ```
   cd frontend
   ```

2. 安装依赖：
   ```
   npm install
   ```

3. 运行开发服务器：
   ```
   npm start
   ```
   前端将在 http://localhost:3000 运行

## 使用方法

1. 打开网页 http://localhost:3000
2. 首次使用时，点击"初始化示例数据库"按钮
3. 点击上传区域选择宠物图片
4. 点击"开始寻找"按钮
5. 查看匹配结果和联系信息

## 注意事项

- 确保已安装Python 3.7+和Node.js 14+
- 首次运行时需要下载ResNet101预训练模型，可能需要较长时间
- 此系统为MVP（最小可行产品），仅作为概念验证使用 