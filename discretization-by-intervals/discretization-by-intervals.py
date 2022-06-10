import pandas as pd
# load libraries for XML proccessing
import xml.etree.ElementTree as ET

def is_number_repl_isdigit(s):
    """ Returns True is string is a number. """
    return s.replace('.','',1).isdigit()

intervals_dict = {}

# tree = ET.parse('./data/diabetes/intervals.xml')
tree = ET.parse('./data/iris_out2.xml')
root = tree.getroot()
""" for attribute in root.findall('Attribute'):
    name = attribute.find('Name')
    print(name.text)
    if name.text == 'petal length':
        for interval in attribute.findall('Interval'):
            number = interval.find('Number')
            min_value = interval.find('Min').text
            max_value = interval.find('Max').text
            intervals_petal_length['labeled'].append({number.text:pd.Interval(float(min_value), float(max_value), closed='both')})
            intervals_petal_length['unlabeled'].append(pd.Interval(float(min_value), float(max_value), closed='both'))
            print(number.text)
    if name.text == 'petal width':
        for interval in attribute.findall('Interval'):
            number = interval.find('Number')
            min_value = interval.find('Min').text
            max_value = interval.find('Max').text
            intervals_petal_width['labeled'].append({number.text:pd.Interval(float(min_value), float(max_value), closed='both')})
            intervals_petal_width['unlabeled'].append(pd.Interval(float(min_value), float(max_value), closed='both'))
            print(number.text)
    if name.text == 'sepal length':
        for interval in attribute.findall('Interval'):
            number = interval.find('Number')
            min_value = interval.find('Min').text
            max_value = interval.find('Max').text
            intervals_sepal_length['labeled'].append({number.text:pd.Interval(float(min_value), float(max_value), closed='both')})
            intervals_sepal_length['unlabeled'].append(pd.Interval(float(min_value), float(max_value), closed='both'))
            print(number.text)
    if name.text == 'sepal width':
        for interval in attribute.findall('Interval'):
            number = interval.find('Number')
            min_value = interval.find('Min').text
            max_value = interval.find('Max').text
            intervals_sepal_width['labeled'].append({number.text:pd.Interval(float(min_value), float(max_value), closed='both')})
            intervals_sepal_width['unlabeled'].append(pd.Interval(float(min_value), float(max_value), closed='both'))
            print(number.text) """

for attribute in root.findall('Attribute'):
    name = attribute.find('Name')
    print(name.text)
    intervals_dict.update({name.text: {'intervals': [], 'index': {}}})

print('INTERVALS EMPTY: ')
print(intervals_dict)

for attribute in root.findall('Attribute'):
    name = attribute.find('Name')
    print(name.text)
    for interval in attribute.findall('Interval'):
        min_value = interval.find('Min').text
        max_value = interval.find('Max').text
        intervals_dict[name.text]['intervals'].append(pd.Interval(float(min_value), float(max_value), closed='both'))

print('INTERVALS INTERVALS: ')
print(intervals_dict)

# intervals_dict['sepal length']['index'] = pd.IntervalIndex(intervals_dict['sepal length']['intervals'])

for key, value in intervals_dict.items():
    value['index'] = pd.IntervalIndex(value['intervals'])

print('INTERVALS INTERVALS INDEX: ')
print(intervals_dict)



data = pd.read_csv('./data/input_iris_fix_enc.csv', sep=';', dtype = str)
# data = pd.read_csv('./data/diabetes/diabetes-for-discret-service.csv', sep=';', dtype = str)

columns_names_list = data.columns.values.tolist()

for col_name in columns_names_list:
    if col_name not in ['Object', 'Class']:
        for item_index,item in enumerate(data[col_name]):
            print(item)
            print(type(item))
            if type(item) is not float:
                if is_number_repl_isdigit(item):
                    if isinstance(intervals_dict[col_name]['index'].get_loc(float(item)), slice):
                        data.loc[item_index, col_name] = int(intervals_dict[col_name]['index'].get_loc(float(item)).start) + 1
                    else:
                        data.loc[item_index, col_name] = intervals_dict[col_name]['index'].get_loc(float(item)) + 1
            else:
                data.loc[item_index, col_name] = ''




# for item_index,item in enumerate(data['petal length']):

#     if type(item) is not float:
#         if is_number_repl_isdigit(item):
#             if isinstance(index_petal_length.get_loc(float(item)), slice):
#                 data.loc[item_index, 'petal length'] = int(index_petal_length.get_loc(float(item)).start) + 1
#                 print("slice! : " + str(index_petal_length.get_loc(float(item)).start + 1))
#             else:
#                 data.loc[item_index, 'petal length'] = index_petal_length.get_loc(float(item)) + 1
#     else:
#         data.loc[item_index, 'petal length'] = ''

# for item_index,item in enumerate(data['petal width']):
#     # print('item:')
#     # print(item)
#     # print(type(item))

#     if type(item) is not float:
#         if is_number_repl_isdigit(item):
#             if isinstance(index_petal_width.get_loc(float(item)), slice):
#                 data.loc[item_index, 'petal width'] = int(index_petal_width.get_loc(float(item)).start) + 1
#                 print("slice! : " + str(index_petal_width.get_loc(float(item)).start + 1))
#             else:
#                 data.loc[item_index, 'petal width'] = index_petal_width.get_loc(float(item)) + 1
#     else:
#         data.loc[item_index, 'petal width'] = ''

# for item_index,item in enumerate(data['sepal length']):
#     # print('item:')
#     # print(item)
#     # print(type(item))

#     if type(item) is not float:
#         if is_number_repl_isdigit(item):
#             if isinstance(index_sepal_length.get_loc(float(item)), slice):
#                 data.loc[item_index, 'sepal length'] = int(index_sepal_length.get_loc(float(item)).start) + 1
#                 print("slice! : " + str(index_sepal_length.get_loc(float(item)).start + 1))
#             else:
#                 data.loc[item_index, 'sepal length'] = index_sepal_length.get_loc(float(item)) + 1
#     else:
#         data.loc[item_index, 'sepal length'] = ''

# for item_index,item in enumerate(data['sepal width']):
#     # print('item:')
#     # print(item)
#     # print(type(item))

#     if type(item) is not float:
#         if is_number_repl_isdigit(item):
#             if isinstance(index_sepal_width.get_loc(float(item)), slice):
#                 data.loc[item_index, 'sepal width'] = int(index_sepal_width.get_loc(float(item)).start) + 1
#                 print("slice! : " + str(index_sepal_width.get_loc(float(item)).start + 1))
#             else:
#                 data.loc[item_index, 'sepal width'] = index_sepal_width.get_loc(float(item)) + 1
#     else:
#         data.loc[item_index, 'sepal width'] = ''

# data['petal length'] = data['petal length'].astype(int)
# data['petal width'] = data['petal width'].astype(int)
# data['sepal length'] = data['sepal length'].astype(int)
# data['sepal width'] = data['sepal width'].astype(int)

# data['petal length'] = data['petal length'].astype(str)
# data['petal width'] = data['petal width'].astype(str)
# data['sepal length'] = data['sepal length'].astype(str)
# data['sepal width'] = data['sepal width'].astype(str)

data.to_csv("./data/test.csv", index=False, sep=';')