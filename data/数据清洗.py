import pandas as pd

def replace_scenic_name(df, column_name, old_name, new_name):
    
    # 记录替换前的数量
    count_before = (df[column_name] == old_name).sum()
    
    # 执行替换
    df[column_name] = df[column_name].replace(old_name, new_name)
    
    # 记录替换后的数量
    count_after = (df[column_name] == old_name).sum()
    
    print(f"成功将 {count_before} 个 '{old_name}' 替换为 '{new_name}'")
    print(f"替换后仍有 {count_after} 个 '{old_name}' 存在")
    
    return df

df = pd.read_csv('sentiment_data.csv')
df = replace_scenic_name(df, '景区名称', '嵩山风景名胜区', '嵩山')

import pandas as pd
import numpy as np

def remove_unknown_scenic_areas(df, column_name='景区名称'):
    """
    去除未知景区数据
    
    Args:
        df: pandas DataFrame
        column_name: 景区名称列名，默认为 '景区名称'
    
    Returns:
        处理后的 DataFrame
    """
    # 定义可能表示未知景区的值
    unknown_values = ['未知景区']
    
    # 记录处理前的行数
    original_count = len(df)
    
    # 过滤掉未知景区
    # 首先处理空值和NaN
    df_cleaned = df.dropna(subset=[column_name])
    
    # 过滤掉包含未知值的行
    pattern = '|'.join(unknown_values)
    df_cleaned = df_cleaned[~df_cleaned[column_name].str.contains(pattern, case=False, na=False)]
    
    # 过滤掉空字符串
    df_cleaned = df_cleaned[df_cleaned[column_name].str.strip() != '']
    
    # 记录处理后的行数
    cleaned_count = len(df_cleaned)
    
    print(f"原始数据行数: {original_count}")
    print(f"处理后数据行数: {cleaned_count}")
    print(f"移除的未知景区数据行数: {original_count - cleaned_count}")
    
    return df_cleaned

df.to_csv('sentiment_data.csv', index=False,encoding='utf-8-sig')