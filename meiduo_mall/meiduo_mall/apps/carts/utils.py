import base64
import pickle
from django_redis import get_redis_connection



# 定义合并cookie和redis中的购物车商品
def hebing_cookie_redis_cart(request, user, response):
    # 将cookie中商品合并到redis, 商品数量和商品勾选状态以cookie为准

    # 获取cookie中的商品
    cookie_cart = request.COOKIES.get('cart')
    # 解析
    if cookie_cart:
        cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
    else:
        cookie_cart_dict = {}
    if  not cookie_cart_dict:
        return response

    # 获取redis中的商品
    redis_conn = get_redis_connection('cart')
    redis_cart = redis_conn.hgetall('cart_%s' % user.id)
    pl = redis_conn.pipeline()

    # redis_cart = {
    #     商品sku_id  bytes字节类型:  商品数量  bytes字节类型
    #     商品sku_id  bytes字节类型:  商品数量  bytes字节类型
    # ...
    # }
    redis_cart_dict = {}
    for sku_id, count in redis_cart.items():
        # 把键值对转成整型
        redis_cart_dict[int(sku_id)] = int(count)

    # 把cookie中商品数据和并到redis中去,如果有重复的商品, 以cookie中的为准
    # cookie_cart_dict = {
    #     sku_id: {
    #         count: 10
    #         selected: True
    #     },
    #     sku_id: {
    #         count: 20
    #         selected: False
    #     }
    # }

    # redis中set中的sku_id为bytes类型, cookie中取出来的字典中sku_id为整型

    # 记录redis中勾选状态应该增加的sku_id
    redis_cart_selected_add = []
    # 记录redis中勾选状态应该删除的sku_id
    redis_cart_selected_delete = []

    # 这里的user.id只有一个,也就是操作的是一个已登陆的用户
    # 遍历cookie中的商品, 取出商品id和数量勾选状态的字典
    for sku_id, count_selected_dict in cookie_cart_dict.items():
        # 1, 如果cookie中的商品在redis也有, 则把商品数量覆盖redis中的商品数量
        # 2, 如果cookie中的商品在redis中没有, 则添加到redis并附上商品数量
        redis_cart_dict[sku_id] = count_selected_dict['count']

        # 获取勾选状态
        selected = count_selected_dict['selected']

        sku_id = str(sku_id).encode()

        if selected:
            # 如果在cookie中,该sku_id是勾选, 把它添加到add中
            redis_cart_selected_add.append(sku_id)
        else:
            # 如果在cookie中,该sku_id是未勾选, 把它添加到delete中
            redis_cart_selected_delete.append(sku_id)

    # 更新到redis
    # cookie和redis中的购物车商品都不为空, 更新hash数据
    if redis_cart_dict:
        pl.hmset('cart_%s' % user.id, redis_cart_dict)
    # 把cookie中勾选状态的商品全在redis中设置成勾选
    if redis_cart_selected_add:
        pl.sadd('cart_selected_%s' % user.id, *redis_cart_selected_add)
    # 把cookie中未勾选状态的商品全在redis中设置成未勾选
    if redis_cart_selected_delete:
        pl.srem('cart_selected_%s' % user.id, *redis_cart_selected_delete)

    pl.execute()

    # 删出cookie中的购物车数据
    response.delete_cookie('cart')
    return response

