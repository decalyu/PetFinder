import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path
import logging
import re
import time
from urllib.parse import urljoin

class DevoreShelterCrawler:
    def __init__(self):
        self.base_url = "https://24petconnect.com"
        self.search_url = f"{self.base_url}/SBCO1Adopt"
        self.save_dir = Path("backend/database/24petconnect")
        self.images_dir = self.save_dir / "images"
        self.pets_info_file = self.save_dir / "pets_info.json"
        
        # 创建必要的目录
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 配置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_pet_info(self, pet_card):
        try:
            # 从Meet元素中提取名字和ID
            meet_elem = pet_card.find('div', class_='line_Meet')
            if not meet_elem:
                self.logger.error("未找到Meet元素")
                return None
            
            meet_text = meet_elem.text.strip()
            self.logger.info(f"Meet文本: {meet_text}")
            
            # 提取括号中的ID
            id_match = re.search(r'\(([^)]+)\)', meet_text)
            if not id_match:
                self.logger.error("未找到ID")
                return None
            pet_id = id_match.group(1)
            
            # 提取名字 - 移除"Meet: "前缀和ID部分
            name = meet_text.replace("Meet:", "").split('(')[0].strip()
            name = re.sub(r'^(URGENT\s+)?(MED\s+)?(ADOPT\s+)?', '', name).strip()
            
            # 提取其他信息
            location = "San Bernardino County - Devore Shelter"
            gender = pet_card.find('div', class_='line_Gender')
            breed = pet_card.find('div', class_='line_Breed')
            age = pet_card.find('div', class_='line_Age')
            size = pet_card.find('div', class_='line_Size')
            color = pet_card.find('div', class_='line_Color')
            days_in_care = pet_card.find('div', class_='line_DaysinOurCare')
            shelter_arrival = pet_card.find('div', class_='line_ShelterArrival')
            found_near = pet_card.find('div', class_='line_FoundNear')
            
            # 检查是否所有必要的元素都存在
            if not all([gender, breed, age, size, color, days_in_care, shelter_arrival, found_near]):
                self.logger.error("缺少必要的信息元素")
                return None
                
            # 获取图片URL
            img_elem = pet_card.find('img')
            if not img_elem:
                self.logger.error("未找到图片元素")
                return None
            img_url = img_elem.get('src', '')
            if not img_url:
                self.logger.error("未找到图片URL")
                return None
            
            # 构建完整的图片URL
            img_url = urljoin(self.base_url, img_url)
            
            # 保存图片
            image_path = self.save_image(img_url, pet_id)
            if not image_path:
                self.logger.error("保存图片失败")
                return None
            
            pet_info = {
                'name': name,  # 使用宠物的实际名字
                'location': location,
                'gender': gender.text.replace("Gender:", "").strip(),
                'breed': breed.text.replace("Breed:", "").strip(),
                'age': age.text.replace("Age:", "").strip(),
                'website': 'www.sbcounty.gov/acc',
                'phone': '(909) 386-9820',
                'address': '19777 Shelter Way, Devore, CA 92407',
                'days_in_care': days_in_care.text.replace("Days in Our Care:", "").strip(),
                'arrival_date': shelter_arrival.text.replace("Shelter Arrival:", "").strip(),
                'found_near': found_near.text.replace("Found Near:", "").strip(),
                'image_url': img_url,
                'id': pet_id,
                'local_image': image_path
            }
            
            self.logger.info(f"成功提取宠物信息: {pet_info}")
            return pet_info
            
        except Exception as e:
            self.logger.error(f"提取宠物信息时出错: {str(e)}")
            return None

    def save_image(self, image_url, pet_id):
        """保存宠物图片"""
        if not image_url:
            return None
            
        try:
            response = self.session.get(image_url)
            response.raise_for_status()
            
            # 生成文件名
            filename = f"{pet_id}.jpg"
            filepath = self.images_dir / filename
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            return filename
            
        except Exception as e:
            self.logger.error(f"保存图片时出错 {image_url}: {str(e)}")
            return None

    def crawl_page(self, page=1):
        """抓取指定页面的宠物信息"""
        try:
            url = self.search_url
            if page > 1:
                url = f"{url}?page={page}"
                
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            pet_cards = soup.find_all('div', class_='gridResult')
            self.logger.info(f"找到 {len(pet_cards)} 个宠物卡片")
            
            pets = []
            for pet_card in pet_cards:
                pet_info = self.get_pet_info(pet_card)
                if pet_info:
                    pets.append(pet_info)
            
            return pets
            
        except Exception as e:
            self.logger.error(f"抓取页面 {page} 时出错: {str(e)}")
            return []

    def crawl(self):
        """抓取第一页的宠物信息"""
        all_pets = []
        
        try:
            # 只抓取第一页
            pets = self.crawl_page(page=1)
            if pets:
                all_pets.extend(pets)
                self.logger.info(f"成功从第1页抓取了 {len(pets)} 只宠物信息")
            
            # 保存所有宠物信息到JSON文件
            if all_pets:
                with open(self.pets_info_file, 'w', encoding='utf-8') as f:
                    json.dump(all_pets, f, ensure_ascii=False, indent=2)
                self.logger.info(f"成功保存了 {len(all_pets)} 只宠物信息到 {self.pets_info_file}")
            else:
                self.logger.warning("未找到任何宠物信息")
                
        except Exception as e:
            self.logger.error(f"抓取过程中出错: {str(e)}")
            
        return all_pets

if __name__ == "__main__":
    crawler = DevoreShelterCrawler()
    pets = crawler.crawl()
    print(f"找到 {len(pets)} 个宠物") 