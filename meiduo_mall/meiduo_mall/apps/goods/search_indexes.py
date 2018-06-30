from haystack import indexes
from .models import SKU

                    # 引入索引类具备的功能，# 具备索引能力
class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    '''SKU索引数据模型类'''

    # document=True，表名该字段是主要进行关键字查询的字段，
    # 该字段的索引值可以由多个数据库模型类字段组成
    # use_template=True表示后续检索字段通过模板来指明。
    text = indexes.CharField(document=True, use_template=True) # 传递关键字

    # 下面这些字段是为了序列化器映射前端需要用到的字段而添加的。（因为序列化器继承自HaystackSerializer）
    # 这些字段也可以用于关键字检索， 但不能跨字段查询了，每个字段仅把其对应的数据建立索引。
    id = indexes.IntegerField(model_attr='id')
    name = indexes.CharField(model_attr='name')
    price = indexes.CharField(model_attr='price')
    default_image_url = indexes.CharField(model_attr='default_image_url')
    comments = indexes.IntegerField(model_attr='comments')

    def get_model(self):
        '''返回建立索引的模型类'''
        return SKU

    def index_queryset(self, using=None):
        '''只对上架商品建立索引,并返回查询集'''
        return SKU.objects.filter(is_launched = True)
        # return self.get_model().objects.filter(is_launched = True)