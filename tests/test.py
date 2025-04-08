from src.agentapi.utils.dbtool import redis_template


def test_redis_connection(redis_client):
    """
    测试 Redis 连接是否正常
    :param redis_client: Redis 客户端实例
    :return: None
    """
    try:
        # 测试连接是否正常
        response = redis_client.ping()
        if response:
            print("Redis 连接成功")
        else:
            print("Redis 连接失败")

        # 测试写入和读取数据
        test_key = "test_key"
        test_value = "test_value"
        redis_client.set(test_key, test_value)
        retrieved_value = redis_client.get(test_key)

        if retrieved_value == test_value:
            print(f"Redis 写入和读取测试成功: {test_key} -> {retrieved_value}")
        else:
            print("Redis 写入和读取测试失败")

    except Exception as e:
        print(f"Redis 测试失败: {e}")


# 调用测试函数
if __name__ == "__main__":
    test_redis_connection(redis_template)
