from re import X
import pandas as pd
# load libraries for XML proccessing
import xml.etree.ElementTree as ET

intervals_petal_length = {
    'labeled':[],
    'unlabeled':[]
}

intervals_petal_width = {
    'labeled':[],
    'unlabeled':[]
}

intervals_sepal_length = {
    'labeled':[],
    'unlabeled':[]
}

intervals_sepal_width = {
    'labeled':[],
    'unlabeled':[]
}

tree = ET.parse('./data/iris_out2.xml')
root = tree.getroot()
for attribute in root.findall('Attribute'):
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
            print(number.text)

print('intervals_petal_length:')
print(intervals_petal_length)
index_petal_length = pd.IntervalIndex(intervals_petal_length['unlabeled'])

print('intervals_petal_width:')
print(intervals_petal_width)
index_petal_width = pd.IntervalIndex(intervals_petal_width['unlabeled'])

print('intervals_sepal_length:')
print(intervals_sepal_length)
index_sepal_length = pd.IntervalIndex(intervals_sepal_length['unlabeled'])

print('intervals_sepal_width:')
print(intervals_sepal_width)
index_sepal_width = pd.IntervalIndex(intervals_sepal_width['unlabeled'])



# print("\nInteger location for requested label...index_petal_length\n", index_petal_length.get_loc(2.0620000000000003))
# if isinstance(index_petal_length.get_loc(2.0620000000000003), slice):
#     print(index_petal_length.get_loc(2.0620000000000003).start)
# print("\nInteger location for requested label...index_petal_length\n", intervals_petal_length['labeled'][index_petal_length.get_loc(1.4)])

data = pd.read_csv('./data/input_iris_fix_enc.csv', sep=';')

for item_index,item in enumerate(data['petal length']):
    # data.set_value(item_index, 'petal length',index_petal_length.get_loc(item))
    print(item)
    print(index_petal_length.get_loc(item))
    if isinstance(index_petal_length.get_loc(item), slice):
        data.loc[item_index, 'petal length'] = int(index_petal_length.get_loc(item).start) + 1
        print("slice! : " + str(index_petal_length.get_loc(item).start + 1))
    else:
        data.loc[item_index, 'petal length'] = index_petal_length.get_loc(item) + 1

for item_index,item in enumerate(data['petal width']):
    # data.set_value(item_index, 'petal length',index_petal_length.get_loc(item))
    print(item)
    print(index_petal_width.get_loc(item))
    if isinstance(index_petal_width.get_loc(item), slice):
        data.loc[item_index, 'petal width'] = int(index_petal_width.get_loc(item).start) + 1
        print("slice! : " + str(index_petal_width.get_loc(item).start + 1))
    else:
        data.loc[item_index, 'petal width'] = index_petal_width.get_loc(item) + 1

for item_index,item in enumerate(data['sepal length']):
    print(item)
    print(index_sepal_length.get_loc(item))
    if isinstance(index_sepal_length.get_loc(item), slice):
        data.loc[item_index, 'sepal length'] = int(index_sepal_length.get_loc(item).start) + 1
        print("slice! : " + str(index_sepal_length.get_loc(item).start + 1))
    else:
        data.loc[item_index, 'sepal length'] = index_sepal_length.get_loc(item) + 1

for item_index,item in enumerate(data['sepal width']):
    print(item)
    print(index_sepal_width.get_loc(item))
    if isinstance(index_sepal_width.get_loc(item), slice):
        data.loc[item_index, 'sepal width'] = int(index_sepal_width.get_loc(item).start) + 1
        print("slice! : " + str(index_sepal_width.get_loc(item).start + 1))
    else:
        data.loc[item_index, 'sepal length'] = index_sepal_width.get_loc(item) + 1

data['petal length'] = data['petal length'].astype(int)
data['petal width'] = data['petal width'].astype(int)
data['sepal length'] = data['sepal length'].astype(int)
data['sepal width'] = data['sepal width'].astype(int)

data.to_csv("./data/test.csv", index=False, sep=';')


# print(data.columns)
# print(data['sepal length'][0])





# interval1 = pd.Interval(50, 75)
# interval2 = pd.Interval(50, 75)
# index = pd.IntervalIndex([interval2, interval1])
# Get integer location for requested label
# print("\nInteger location for requested label...\n",index.get_loc(75))
# dict_interval = {pd.Interval(50, 75):"1",pd.Interval(50, 75):"2"}

# intervals_sepal_length = [{"1":pd.Interval(4.3, 4.8759999999999994)},{"2":pd.Interval(4.8759999999999994, 5.272)}]

# index_sepal_length = pd.IntervalIndex([intervals_sepal_length[0]["1"], intervals_sepal_length[1]["2"]])

# print("\nInteger location for requested label...\n", index_sepal_length.get_loc(5.1))
