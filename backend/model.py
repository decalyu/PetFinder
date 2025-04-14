import torch
import torchvision.models as models
from torchvision.models import ResNet101_Weights
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os
import cv2
from tqdm import tqdm
import io
import heapq  # 用于实现前K个最相似图像的查找
import time
import pickle

# Initialize the ResNet101 pre-trained model (remove the final classification layer)
model = models.resnet101(weights=ResNet101_Weights.DEFAULT)  # Updated from pretrained=True
model = torch.nn.Sequential(*list(model.children())[:-1])  # Remove the classification layer
model.eval()

# Image preprocessing transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # ImageNet normalization
])

def preprocess_image(image_path):
    """Enhanced image preprocessing for better feature extraction"""
    try:
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            return None
            
        # 转换为RGB（模型使用RGB格式）
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 亮度和对比度自适应调整
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        # 转换回PIL图像格式
        pil_image = Image.fromarray(enhanced)
        return pil_image
    except Exception as e:
        print(f"预处理图像时出错: {str(e)}")
        # 如果预处理失败，尝试直接打开原始图像
        try:
            return Image.open(image_path).convert("RGB")
        except:
            return None

def extract_color_histogram(image, bins=(8, 8, 8)):
    """提取图像的HSV颜色直方图"""
    # 确保输入是NumPy数组
    if isinstance(image, Image.Image):
        image_np = np.array(image)
    else:
        image_np = image
        
    # 转换到HSV颜色空间
    hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
    # 计算直方图
    hist = cv2.calcHist([hsv], [0, 1, 2], None, bins, [0, 180, 0, 256, 0, 256])
    # 归一化直方图
    cv2.normalize(hist, hist)
    return hist.flatten()

def histogram_similarity(hist1, hist2):
    """计算两个直方图的相似度（使用巴氏距离并转换为相似度）"""
    # 巴氏距离越小表示越相似，所以用1减去距离转换为相似度
    dist = cv2.compareHist(hist1.reshape(-1, 1), hist2.reshape(-1, 1), cv2.HISTCMP_BHATTACHARYYA)
    return 1.0 - dist  # 转换为相似度

def extract_feature(image_path):
    """ Extract feature vector from an image """
    try:
        # 使用增强的预处理
        image = preprocess_image(image_path)
        if image is None:
            print(f"无法处理图像 {image_path}")
            return None, None
            
        # 提取深度特征
        image_tensor = transform(image).unsqueeze(0)  # Add batch dimension
        with torch.no_grad():
            feature = model(image_tensor)
        
        # 提取颜色直方图
        color_hist = extract_color_histogram(image)
        
        return feature.squeeze().numpy(), color_hist  # 返回两种特征
    except Exception as e:
        print(f"处理图像时出错 {image_path}: {e}")
        return None, None

def cosine_similarity(vec1, vec2):
    """ Compute cosine similarity between two feature vectors """
    sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    return float(sim)  # 确保返回标准Python float，而不是numpy.float32

def combined_similarity(deep_feat1, color_hist1, deep_feat2, color_hist2, alpha=0.7):
    """计算综合相似度，alpha控制深度特征的权重"""
    if deep_feat1 is None or deep_feat2 is None:
        return 0
        
    # 计算深度特征相似度（余弦相似度）
    deep_sim = cosine_similarity(deep_feat1, deep_feat2)
    
    # 计算颜色直方图相似度
    color_sim = histogram_similarity(color_hist1, color_hist2)
    
    # 组合两种相似度
    combined_sim = alpha * deep_sim + (1 - alpha) * color_sim
    return combined_sim

def find_most_similar(image_path, folder_path, top_k=1, alpha=0.7, use_cache=True):
    """ Find the most similar image in a given folder """
    start_time = time.time()
    
    # 提取查询图像特征
    query_deep_feature, query_color_hist = extract_feature(image_path)
    if query_deep_feature is None:
        print(f"Failed to extract features from query image: {image_path}")
        return [], []
    
    # 加载或构建特征缓存
    if use_cache:
        features_cache = load_or_build_features_cache(folder_path)
    else:
        features_cache = None
    
    # 使用字典存储相似度
    similarity_dict = {}
    
    # 获取有效图像文件列表
    image_files = [f for f in os.listdir(folder_path) 
                  if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    
    print(f"Searching through {len(image_files)} images...")
    
    try:
        # 使用缓存进行搜索
        if use_cache and features_cache:
            for filename, features in features_cache.items():
                try:
                    # 确保特征数据有效
                    if not isinstance(features, dict):
                        continue
                    
                    db_deep_feature = features.get('deep_feature')
                    db_color_hist = features.get('color_hist')
                    
                    if db_deep_feature is None or db_color_hist is None:
                        continue
                    
                    # 计算综合相似度
                    similarity = combined_similarity(
                        query_deep_feature, query_color_hist,
                        db_deep_feature, db_color_hist,
                        alpha
                    )
                    
                    # 存储相似度和路径
                    file_path = os.path.join(folder_path, filename)
                    similarity_dict[file_path] = similarity
                    
                except Exception as e:
                    print(f"Error processing cached file {filename}: {e}")
                    continue
        else:
            # 不使用缓存，实时计算特征（较慢）
            for filename in image_files:
                try:
                    file_path = os.path.join(folder_path, filename)
                    db_deep_feature, db_color_hist = extract_feature(file_path)
                    
                    if db_deep_feature is not None and db_color_hist is not None:
                        # 计算综合相似度
                        similarity = combined_similarity(
                            query_deep_feature, query_color_hist,
                            db_deep_feature, db_color_hist,
                            alpha
                        )
                        
                        # 存储相似度和路径
                        similarity_dict[file_path] = similarity
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    continue
        
        # 找出最相似的图片
        if similarity_dict:
            # 使用max函数直接找到相似度最高的图片
            best_path = max(similarity_dict.items(), key=lambda x: x[1])
            paths = [best_path[0]]
            similarities = [best_path[1]]
        else:
            paths = []
            similarities = []
        
    except Exception as e:
        print(f"Error during similarity search: {e}")
        return [], []
    
    end_time = time.time()
    print(f"Found most similar image in {end_time - start_time:.2f} seconds")
    return paths, similarities

def load_or_build_features_cache(folder_path, force_rebuild=False):
    """加载或构建特征缓存"""
    cache_file = os.path.join(folder_path, 'features_cache.pkl')
    
    # 检查缓存文件是否存在且不强制重建
    if os.path.exists(cache_file) and not force_rebuild:
        try:
            print("Loading feature cache...")
            with open(cache_file, 'rb') as f:
                cache = pickle.load(f)
            
            # 验证缓存数据
            if cache and isinstance(cache, dict):
                print(f"Cache loaded successfully with {len(cache)} images")
                return cache
            else:
                print("Invalid cache format, rebuilding...")
                force_rebuild = True
        except Exception as e:
            print(f"Error loading cache: {e}, rebuilding...")
            force_rebuild = True
    
    # 如果需要重建缓存
    if force_rebuild or not os.path.exists(cache_file):
        print("Building feature cache...")
        cache = {}
        
        # 获取所有图像文件
        image_files = [f for f in os.listdir(folder_path) 
                      if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        
        # 处理每个图像并缓存特征
        for filename in tqdm(image_files, desc="Extracting features"):
            file_path = os.path.join(folder_path, filename)
            deep_feature, color_hist = extract_feature(file_path)
            
            if deep_feature is not None:
                cache[filename] = {
                    'deep_feature': deep_feature,
                    'color_hist': color_hist
                }
        
        # 保存缓存
        with open(cache_file, 'wb') as f:
            pickle.dump(cache, f)
        
        print(f"Feature cache built with {len(cache)} images")
        return cache
    
    return {}

# 只有当直接运行此脚本时才执行示例代码
if __name__ == "__main__":
    # 🐶🐱 Example: Find the most similar pet photo
    database_folder = "/Users/alex/Desktop/Pet-Finder/petcode/backend/database"  # Folder containing stored pet images
    query_image = "/Users/alex/Desktop/Pet-Finder/petcode/backend/uploads/Unknown-1.jpeg"  # Input pet image to compare

    print(f"\n🔍 Finding most similar pet to {os.path.basename(query_image)}...")
    similar_paths, similarity_scores = find_most_similar(query_image, database_folder)

    # ===================== OUTPUT RESULTS =====================
    print("\n" + "=" * 50)
    print(f" 📁 Database Folder : {database_folder}")
    print(f" 📷 Query Image : {query_image}")
    print("-" * 50)
    
    for i, (path, score) in enumerate(zip(similar_paths, similarity_scores)):
        print(f" ✅ 第{i+1}相似宠物照片: {path}")
        print(f" 🔥 相似度分数: {score:.2f}")
        print("-" * 30)
        
    print("=" * 50 + "\n")

    # 显示最相似的图像
    if similar_paths:
        query_img = cv2.imread(query_image)
        
        if query_img is not None:
            cv2.imshow("Query Image", cv2.resize(query_img, (300, 300)))
            
            for i, path in enumerate(similar_paths):
                result_img = cv2.imread(path)
                if result_img is not None:
                    cv2.imshow(f"Similar Image #{i+1}", cv2.resize(result_img, (300, 300)))
            
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Error: Unable to display images.")