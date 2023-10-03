import os
import pandas as pd



#USER_SETTINGS
xls_file = r'C:\_Workspace\TASK\Геокодирование\Сообщения\Наркосообщения 2 кв 2023.xls'
#xls_file = r'C:\_Workspace\TASK\Геокодирование\Отравления\Отравления_2кв23.xlsx'
type = 2 # 1 - Отравления
         # 2 - Сообщения




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
                    'Кроншт.': 'Кронштадский',
                    'Курортн.': 'Курортный',
                    'Моск.': 'Московский',
                    'Невск.': 'Невский',
                    'Петрогр.': 'Петроградский',
                    'Петродв.': 'Петродворцовый',
                    'Пушк.': 'Пушкинский',
                    'Фрунз.': 'Фрунзенский',
                    'Центр.': 'Центральный',
                    'Приморс.': 'Приморский',
                    'Приморс.': 'Приморский',
                     
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

        
if __name__ == "__main__"    :       
    os.chdir(os.path.dirname(xls_file))
    src_file = os.path.basename(xls_file)
    df = pd.read_excel(xls_file) 
    df['set_id'] = df.index + 1
    ext_len= len(src_file.split('.')[1])+1
    df.to_csv(src_file[:-ext_len]+'_full.csv', index=False, sep='\t')
    
    if type == 1:
        df = xlsx_type_1(df)
        #df.to_csv(src_file[:-ext_len]+'_ID.csv', index=False, columns=['set_id', 'city', 'Street', 'HouseNum'])
        df['Mesto'] = df['city'].astype(str)+', '+df['Street'].astype(str)+', '+ df['HouseNum'].astype(str)+', '+ df['District']+' район'

        
    elif type == 2:
        cols = ['set_id', 'city', 'Mesto','District']
        df = xlsx_type_2(df, cols)
        #df.to_csv(src_file[:-ext_len]+'_ID.csv', index=False, columns=['set_id', 'Mesto', 'District'], sep='\t')
        df['District'] = df['District'].astype(str)+' район'
        df['Mesto'] = df['city'].astype(str)+', '+df['Mesto'].astype(str)+', '+ df['District']

        
    else:
        print("не указан формат входных данных type")
        
    cols = ['set_id', 'Mesto']
    split_by_950(df, src_file, cols, ext_len)