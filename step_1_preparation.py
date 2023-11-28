import os
import pandas as pd
import json

# USER_SETTINGS 1
xls_file = r'C:\_Workspace\TASK\Геокодирование\Сообщения\temp\НС_3кв23_v3.xlsx'
# USER_SETTINGS 2
type = 2 # 1 - Отравления
         # 2 - Сообщения
# USER_SETTINGS 3
street_dict_file = r'C:\_Workspace\TASK\Геокодирование\Tools\Antinar_GeoLocator\street_dict_file.txt'


def make_street_dict(file):
    with open(file, encoding="utf-8") as f:
        data = f.read()
        street_dict = json.loads(data)
    return street_dict

def xlsx_type_1(df):
    df['city'] = 'Санкт-Петербург' 
    district_dict = {
                    'Адмир.': 'Адмиралтейский',
                    'Васил.': 'Василеостровский',
                    'Выб.': 'Выборгский',
                    'Калин.': 'Калининский',
                    'Киров.': 'Кировский',
                    'Колп.': 'Колпинский',
                    'Красногв.': 'Красногвардейский',
                    'Краснос.': 'Красносельский',
                    'Кроншт.': 'Кронштадтский',
                    'Курортн.': 'Курортный',
                    'Моск.': 'Московский',
                    'Невск.': 'Невский',
                    'Петрогр.': 'Петроградский',
                    'Петродв.': 'Петродворцовый',
                    'Пушк.': 'Пушкинский',
                    'Фрунз.': 'Фрунзенский',
                    'Центр.': 'Центральный',
                    'Приморс.': 'Приморский',
                    'Прим.': 'Приморский',
                     
                     }
    df = df.replace({"District": district_dict})
    df_crop = df[['set_id', 'city', 'Street', 'HouseNum', 'District']].copy()
    df_crop = df_crop[(df_crop.Street != 'Не указана')] 

    return df_crop


def xlsx_type_2(df, cols):
    df['city'] = 'Санкт-Петербург' 
    df_crop = df[cols].copy()
    return df_crop


def split_by_950(df, src_file, cols, ext_len):
    # Разбиваем по 950 штук, чтобы попадать в лимит 1000
    size = 950
    list_of_dfs = (df.loc[i:i+size-1,:] for i in range(0, len(df),size))
    df_number = 1
    for i in list_of_dfs:
        i.to_csv(src_file[:-ext_len]+'_part'+str(df_number)+'.csv', index=False, columns=cols, header=None, sep='\t')
        df_number += 1

def find_house_num_in_messages_type_2(df):
    df = df.join(df.Mesto.str.extract('(?P<Street>\D+) (?P<Number>\d+.*)', expand=True))
    for index, row in df.iterrows():
        #print(row['Street'])
        if pd.isnull(df.loc[index, 'Street']) is True and pd.isnull(df.loc[index, 'Number']) is True : # Если не указан номер дома
            if row['Mesto'].strip() in street_dict:  # и если такая улица есть в словаре исключений, то в зависимости от района приделываем номер дома
                row['Mesto'] = row['Mesto'].strip()
                dt=street_dict[row['Mesto']]
                try:
                    df.loc[index, 'Mesto'] = row['Mesto']+', дом '+str(dt[row['District']])
                except:
                    df.loc[index, 'Mesto'] = row['Mesto']+', дом 1'
            else:  # и если такой улицы НЕТ в словаре исключений, то по умолчанию дом 1
                df.loc[index, 'Mesto'] = row['Mesto']+', дом 1'

    return df

def find_house_num_in_messages_type_1(df):
    for index, row in df.iterrows():
        print(row['Street'], row['HouseNum'])
        if pd.isnull(df.loc[index, 'HouseNum']) is True : # Если не указан номер дома
            if row['Street'].strip() in street_dict:  # и если такая улица есть в словаре исключений, то в зависимости от района приделываем номер дома

                
                row['Street'] = row['Street'].strip()
                dt=street_dict[row['Street']]
                df.loc[index, 'HouseNum'] = 'дом '+str(dt[row['District']])
                print(row['Street'], row['HouseNum'])
            else:  # и если такой улицы НЕТ в словаре исключений, то по умолчанию дом 1
                df.loc[index, 'HouseNum'] = 'дом 1'
                print( df.loc[index, 'HouseNum'])
                print(row['Street'], row['HouseNum'])
    return df
        
if __name__ == "__main__"    :       
    os.chdir(os.path.dirname(xls_file))
    src_file = os.path.basename(xls_file)
    street_dict = make_street_dict(street_dict_file)
    df = pd.read_excel(xls_file) 
    print(df)
    df['set_id'] = df.index + 1
    ext_len= len(src_file.split('.')[1])+1
    df.to_csv(src_file[:-ext_len]+'_full.csv', index=False, sep='\t')
    
    if type == 1:
        df = xlsx_type_1(df)
        #values = {"HouseNum": 1,}
        #df = df.fillna(value=values)
        
        df = find_house_num_in_messages_type_1(df)
        
        df['Mesto'] = df['city'].astype(str)+', '+df['Street'].astype(str)+', '+ df['HouseNum'].astype(str)+', '+ df['District']+' район'

        
    elif type == 2:
        cols = ['set_id', 'city', 'Mesto','District']
        df = xlsx_type_2(df, cols)
        df = find_house_num_in_messages_type_2(df)
        #df.to_csv(r'C:\_Workspace\TASK\Геокодирование\__TEST__.csv')
        df['District'] = df['District'].astype(str)+' район'
        df['Mesto'] = df['city'].astype(str)+', '+df['Mesto'].astype(str)+', '+ df['District']

        
    else:
        print("не указан формат входных данных type")
        
    cols = ['set_id', 'Mesto']
    # df.to_csv(r'C:\_Workspace\TASK\Геокодирование\__TEST__.csv')
    split_by_950(df, src_file, cols, ext_len)