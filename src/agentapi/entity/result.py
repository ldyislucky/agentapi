from fastapi.responses import JSONResponse

def create_response(message: str, data: dict = None) -> JSONResponse:
    """
    创建统一的响应格式
    :param message: 响应的消息内容
    :param data: 响应的数据部分（可选）
    :return: JSONResponse 对象
    """
    response_data = {
        "code": 200,
        "message": "success",
        "data": data or {"message": message}
    }
    return JSONResponse(content=response_data)

