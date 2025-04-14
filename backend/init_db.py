import os
import json
import numpy as np

# 数据库文件夹和文件路径
DATABASE_FOLDER = os.path.join(os.path.dirname(__file__), 'database')
PET_DB_FILE = os.path.join(DATABASE_FOLDER, 'pets_info.json')

# 确保目录存在
os.makedirs(DATABASE_FOLDER, exist_ok=True)

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# 获取数据库文件夹中的图片
image_files = [f for f in os.listdir(DATABASE_FOLDER) 
               if f.lower().endswith(tuple(ALLOWED_EXTENSIONS))]

# 示例宠物品种
breeds = ["Golden Retriever", "Labrador", "Husky", "German Shepherd", 
          "Poodle", "Bulldog", "Beagle", "Siamese Cat", "Persian Cat", 
          "Maine Coon", "Ragdoll", "Bengal Cat", "Tabby Cat"]

# 为每个图片创建示例信息
pet_database = {}
for idx, img_file in enumerate(image_files):
    breed = breeds[idx % len(breeds)]
    pet_database[img_file] = {
        'name': f'Buddy {idx+1}',
        'owner_name': f'Owner {idx+1}',
        'contact': f'Phone: (555) 123-{4000+idx}',
        'description': f'A lovely {breed}. Friendly and loves to play!',
        'breed': breed,
        'age': f'{(idx % 10) + 1} years',
        'location': 'New York, USA'
    }

# 保存到JSON文件
with open(PET_DB_FILE, 'w', encoding='utf-8') as f:
    json.dump(pet_database, f, ensure_ascii=False, indent=4)

print(f"成功初始化 {len(pet_database)} 个宠物记录到 {PET_DB_FILE}") 